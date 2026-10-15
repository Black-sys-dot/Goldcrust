#!/bin/bash
# Stand up Goldcrust in ap-south-1: private Postgres, one app server, HTTPS in front.
# Secrets stay in SSM and .aws-deploy.env. This file does not contain them.
set -euo pipefail
cd "$(dirname "$0")/.."
REGION=ap-south-1
ACCOUNT=733959199566
VPC=vpc-085ec5c50a866224f
SUBNETS="subnet-0610b868e5a987d9f subnet-075c58f9622cc6d80 subnet-0956a8e0ae7953f61"
APP_SUBNET=subnet-0610b868e5a987d9f
IMAGE="$ACCOUNT.dkr.ecr.$REGION.amazonaws.com/goldcrust:1"

umask 077
if [[ ! -f .aws-deploy.env ]]; then
  echo "DB_PASSWORD=$(openssl rand -hex 16)" > .aws-deploy.env
fi
# shellcheck disable=SC1091
source .aws-deploy.env

aws ecr describe-repositories --repository-names goldcrust --region "$REGION" >/dev/null 2>&1 || \
  aws ecr create-repository --repository-name goldcrust --region "$REGION" >/dev/null
echo "ecr ready"

if ! aws rds describe-db-subnet-groups --db-subnet-group-name goldcrust --region "$REGION" >/dev/null 2>&1; then
  aws rds create-db-subnet-group \
    --db-subnet-group-name goldcrust \
    --db-subnet-group-description "Goldcrust private database" \
    --subnet-ids $SUBNETS \
    --region "$REGION" >/dev/null
fi

ensure_sg() {
  local name="$1" desc="$2"
  local id
  id=$(aws ec2 describe-security-groups --region "$REGION" \
    --filters "Name=group-name,Values=$name" "Name=vpc-id,Values=$VPC" \
    --query 'SecurityGroups[0].GroupId' --output text)
  if [[ "$id" == "None" || -z "$id" ]]; then
    id=$(aws ec2 create-security-group --region "$REGION" --group-name "$name" \
      --description "$desc" --vpc-id "$VPC" --query GroupId --output text)
  fi
  echo "$id"
}

DB_SG=$(ensure_sg goldcrust-db "Goldcrust Postgres")
APP_SG=$(ensure_sg goldcrust-app "Goldcrust app")
echo "security groups $DB_SG $APP_SG"

PREFIX=$(aws ec2 describe-managed-prefix-lists --region "$REGION" \
  --filters Name=prefix-list-name,Values=com.amazonaws.global.cloudfront.origin-facing \
  --query 'PrefixLists[0].PrefixListId' --output text)
aws ec2 authorize-security-group-ingress --region "$REGION" --group-id "$APP_SG" \
  --ip-permissions "IpProtocol=tcp,FromPort=8000,ToPort=8000,PrefixListIds=[{PrefixListId=$PREFIX}]" \
  >/dev/null 2>&1 || true
aws ec2 authorize-security-group-ingress --region "$REGION" --group-id "$DB_SG" \
  --protocol tcp --port 5432 --source-group "$APP_SG" >/dev/null 2>&1 || true

if ! aws rds describe-db-instances --db-instance-identifier goldcrust --region "$REGION" >/dev/null 2>&1; then
  aws rds create-db-instance \
    --db-instance-identifier goldcrust \
    --db-instance-class db.t4g.micro \
    --engine postgres \
    --engine-version 16.14 \
    --master-username goldcrust \
    --master-user-password "$DB_PASSWORD" \
    --allocated-storage 20 \
    --storage-type gp3 \
    --storage-encrypted \
    --db-name goldcrust \
    --vpc-security-group-ids "$DB_SG" \
    --db-subnet-group-name goldcrust \
    --backup-retention-period 1 \
    --no-multi-az \
    --no-publicly-accessible \
    --region "$REGION" \
    --tags Key=Project,Value=goldcrust >/dev/null
  echo "rds creating"
else
  echo "rds exists"
fi

echo "building image"
if aws ecr describe-images --repository-name goldcrust --image-ids imageTag=1 --region "$REGION" >/dev/null 2>&1; then
  echo "image already in registry"
else
  mkdir -p /tmp/goldcrust-docker
  printf '%s\n' '{"auths":{}}' > /tmp/goldcrust-docker/config.json
  export DOCKER_CONFIG=/tmp/goldcrust-docker
  export DOCKER_HOST=unix:///home/black/.docker/desktop/docker.sock
  aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"
  nice -n 19 docker build -t goldcrust:1 .
  docker tag goldcrust:1 "$IMAGE"
  docker push "$IMAGE"
fi
echo "image pushed"

echo "waiting for database"
aws rds wait db-instance-available --db-instance-identifier goldcrust --region "$REGION"
ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier goldcrust --region "$REGION" \
  --query 'DBInstances[0].Endpoint.Address' --output text)
echo "database endpoint ready"

put_param() {
  local name="$1" value="$2"
  if aws ssm get-parameter --name "$name" --region "$REGION" >/dev/null 2>&1; then
    aws ssm put-parameter --name "$name" --value "$value" --type SecureString --overwrite --region "$REGION" >/dev/null
  else
    aws ssm put-parameter --name "$name" --value "$value" --type SecureString --region "$REGION" >/dev/null
  fi
}

python3 - << PY
import csv, os, subprocess
row = next(csv.DictReader(open("rzp-key.csv", encoding="utf-8-sig")))
os.environ["RZP_KEY_ID"] = row["key_id"].strip()
os.environ["RZP_KEY_SECRET"] = row["key_secret"].strip()
open("/tmp/goldcrust-keys.env", "w").write("")
PY
# Pass keys without printing them.
RZP_KEY_ID=$(python3 -c 'import csv; print(next(csv.DictReader(open("rzp-key.csv", encoding="utf-8-sig")))["key_id"].strip())')
RZP_KEY_SECRET=$(python3 -c 'import csv; print(next(csv.DictReader(open("rzp-key.csv", encoding="utf-8-sig")))["key_secret"].strip())')
put_param /goldcrust/database_url "postgresql://goldcrust:${DB_PASSWORD}@${ENDPOINT}:5432/goldcrust?sslmode=require"
put_param /goldcrust/rzp_key_id "$RZP_KEY_ID"
put_param /goldcrust/rzp_key_secret "$RZP_KEY_SECRET"
unset RZP_KEY_ID RZP_KEY_SECRET
echo "parameters stored"

ROLE=goldcrust-ec2
if ! aws iam get-role --role-name "$ROLE" >/dev/null 2>&1; then
  aws iam create-role --role-name "$ROLE" --assume-role-policy-document '{
    "Version":"2012-10-17",
    "Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]
  }' >/dev/null
fi
aws iam attach-role-policy --role-name "$ROLE" --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly >/dev/null 2>&1 || true
aws iam attach-role-policy --role-name "$ROLE" --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore >/dev/null 2>&1 || true
aws iam put-role-policy --role-name "$ROLE" --policy-name goldcrust-params --policy-document "{
  \"Version\":\"2012-10-17\",
  \"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"ssm:GetParameter\",\"ssm:GetParameters\"],\"Resource\":\"arn:aws:ssm:${REGION}:${ACCOUNT}:parameter/goldcrust/*\"}]
}" >/dev/null
if ! aws iam get-instance-profile --instance-profile-name "$ROLE" >/dev/null 2>&1; then
  aws iam create-instance-profile --instance-profile-name "$ROLE" >/dev/null
  aws iam add-role-to-instance-profile --instance-profile-name "$ROLE" --role-name "$ROLE"
  sleep 10
fi

AMI=$(aws ec2 describe-images --region "$REGION" --owners amazon \
  --filters Name=name,Values='al2023-ami-*-kernel-6.1-x86_64' Name=state,Values=available \
  --query 'sort_by(Images,&CreationDate)[-1].ImageId' --output text)
echo "ami $AMI"

cat > /tmp/goldcrust-userdata.sh << 'EOF'
#!/bin/bash
set -euo pipefail
exec > /var/log/goldcrust-boot.log 2>&1
dnf install -y docker
systemctl enable --now docker
REGION=ap-south-1
ACCOUNT=733959199566
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"
IMAGE="$ACCOUNT.dkr.ecr.$REGION.amazonaws.com/goldcrust:1"
docker pull "$IMAGE"
DB_URL=$(aws ssm get-parameter --name /goldcrust/database_url --with-decryption --region "$REGION" --query Parameter.Value --output text)
KEY_ID=$(aws ssm get-parameter --name /goldcrust/rzp_key_id --with-decryption --region "$REGION" --query Parameter.Value --output text)
KEY_SECRET=$(aws ssm get-parameter --name /goldcrust/rzp_key_secret --with-decryption --region "$REGION" --query Parameter.Value --output text)
docker rm -f goldcrust || true
docker run -d --name goldcrust --restart unless-stopped -p 8000:8000 \
  -e DATABASE_URL="$DB_URL" \
  -e RZP_KEY_ID="$KEY_ID" \
  -e RZP_KEY_SECRET="$KEY_SECRET" \
  "$IMAGE"
unset DB_URL KEY_ID KEY_SECRET
echo "goldcrust container started"
EOF

if ! aws ec2 describe-instances --region "$REGION" \
  --filters Name=tag:Name,Values=goldcrust Name=instance-state-name,Values=pending,running \
  --query 'Reservations[0].Instances[0].InstanceId' --output text | grep -q '^i-'; then
  INSTANCE=$(aws ec2 run-instances --region "$REGION" \
    --image-id "$AMI" \
    --instance-type t3.micro \
    --subnet-id "$APP_SUBNET" \
    --security-group-ids "$APP_SG" \
    --iam-instance-profile Name="$ROLE" \
    --user-data file:///tmp/goldcrust-userdata.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=goldcrust},{Key=Project,Value=goldcrust}]' \
    --metadata-options 'HttpTokens=required,HttpEndpoint=enabled' \
    --query 'Instances[0].InstanceId' --output text)
else
  INSTANCE=$(aws ec2 describe-instances --region "$REGION" \
    --filters Name=tag:Name,Values=goldcrust Name=instance-state-name,Values=pending,running \
    --query 'Reservations[0].Instances[0].InstanceId' --output text)
fi
echo "instance $INSTANCE"
aws ec2 wait instance-running --instance-ids "$INSTANCE" --region "$REGION"

if ! aws ec2 describe-addresses --region "$REGION" --filters Name=tag:Name,Values=goldcrust \
  --query 'Addresses[0].AllocationId' --output text | grep -q '^eipalloc-'; then
  ALLOC=$(aws ec2 allocate-address --region "$REGION" --domain vpc \
    --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=goldcrust},{Key=Project,Value=goldcrust}]' \
    --query AllocationId --output text)
  aws ec2 associate-address --region "$REGION" --instance-id "$INSTANCE" --allocation-id "$ALLOC" >/dev/null
else
  ALLOC=$(aws ec2 describe-addresses --region "$REGION" --filters Name=tag:Name,Values=goldcrust \
    --query 'Addresses[0].AllocationId' --output text)
  ASSOC=$(aws ec2 describe-addresses --region "$REGION" --allocation-ids "$ALLOC" --query 'Addresses[0].InstanceId' --output text)
  if [[ "$ASSOC" == "None" ]]; then
    aws ec2 associate-address --region "$REGION" --instance-id "$INSTANCE" --allocation-id "$ALLOC" >/dev/null
  fi
fi

PUBLIC_DNS=$(aws ec2 describe-instances --instance-ids "$INSTANCE" --region "$REGION" \
  --query 'Reservations[0].Instances[0].PublicDnsName' --output text)
echo "origin $PUBLIC_DNS"

if [[ ! -f /tmp/goldcrust-cf.json ]]; then
  cat > /tmp/goldcrust-cf.json << EOF
{
  "CallerReference": "goldcrust-$(date +%s)",
  "Comment": "Goldcrust",
  "Enabled": true,
  "PriceClass": "PriceClass_200",
  "HttpVersion": "http2",
  "Origins": {
    "Quantity": 1,
    "Items": [{
      "Id": "goldcrust-app",
      "DomainName": "$PUBLIC_DNS",
      "CustomOriginConfig": {
        "HTTPPort": 8000,
        "HTTPSPort": 443,
        "OriginProtocolPolicy": "http-only",
        "OriginSslProtocols": {"Quantity": 1, "Items": ["TLSv1.2"]},
        "OriginReadTimeout": 30,
        "OriginKeepaliveTimeout": 5
      }
    }]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "goldcrust-app",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 7,
      "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
      "CachedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]}
    },
    "Compress": true,
    "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",
    "OriginRequestPolicyId": "b689b0a8-53d0-40ab-baf2-68738e2966ac"
  },
  "ViewerCertificate": {"CloudFrontDefaultCertificate": true}
}
EOF
  DIST=$(aws cloudfront create-distribution --distribution-config file:///tmp/goldcrust-cf.json \
    --query 'Distribution.{Id:Id,Domain:DomainName}' --output text)
  echo "cloudfront $DIST"
else
  echo "cloudfront config already written"
fi

{
  echo "DB_PASSWORD=$DB_PASSWORD"
  echo "DB_SG=$DB_SG"
  echo "APP_SG=$APP_SG"
  echo "INSTANCE=$INSTANCE"
  echo "PUBLIC_DNS=$PUBLIC_DNS"
  echo "DB_ENDPOINT=$ENDPOINT"
} > .aws-deploy.env
echo "deploy records saved"
