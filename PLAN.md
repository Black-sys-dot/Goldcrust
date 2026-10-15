# Goldcrust plan

Status: captured only. Do not build from this until the two open decisions below are talked through.

Goldcrust is one brand with many branches, in the KFC / McDonald's shape, not a marketplace of different restaurants. The customer storefront is mostly in place. What is missing is the branch network, how an order picks a branch, and the kitchen side that receives that order.

## What exists now

- Customer pages only: home, menu, checkout.
- Cart in the browser. Checkout posts to `POST /api/checkout`.
- Orders sit in memory on the server and are listed at `GET /api/orders`. There is no branch, no mode, and no kitchen view.
- Checkout already shows a pickup slot next to "right now" and "in an hour". That is not the real mode split described below.

## Branch network

Do this before the two order modes matter.

- Pick 10–20 Goldcrust branches across Pune for the demo.
- Put each branch on a map with a real location.
- Every order is assigned to exactly one of these branches.
- That branch is the only place the order details are sent.

## Two order modes

The customer chooses the mode. Both modes record the mode on the order and send the order only to the assigned branch.

### Home delivery (online)

Same idea as Zomato: the food comes to the customer.

- Location comes from the customer's GPS, or from the delivery address if that is the pickup point we measure from.
- The closest Pune branch is chosen automatically.
- The customer cannot pick a branch by hand in this mode.

### Pickup (offline)

The customer collects the order from a branch. This is the in-store / takeaway path, including when they are already at a branch.

- GPS is still read, and the closest branch is the default.
- The customer can override that and choose a branch manually.
- Manual choice covers a bad GPS fix, and the case where they want the parcel from a different branch than the nearest one.

## Two sites

Customer and kitchen are separate products. For this demo they live in the current site so both can be clicked through in one place. They should stay easy to split into two sites later.

### Customer site

What we have now, plus mode choice, location, and branch assignment.

### Kitchen site

A dashboard each branch kitchen uses.

- A kitchen sees only the orders assigned to that branch.
- It is its own set of pages, not a panel buried inside the menu.
- In the demo, link it from the current site. Later it can be served on its own.

## Suggested order of work

Not started. Reorder this after the two open decisions.

1. Clear the two decisions called out below.
2. Define the 10–20 Pune branches and show them on a map.
3. Add the mode choice. Delivery assigns the closest branch from GPS or the delivery location and does not offer a manual pick. Pickup assigns the closest branch and still lets the customer choose another branch.
4. Save mode and branch on the order, and deliver that order only to the chosen branch.
5. Build the kitchen dashboard as its own pages, and link those pages into this demo site.
6. Keep the customer and kitchen surfaces separable so they can become independent sites after the demo.

## Payment

Chosen: Razorpay test mode. Live keys stay off until KYC. A personal UPI QR is not the confirmation path.

Real UPI or card money cannot be accepted, and an order cannot be auto-confirmed from that payment, without KYC. That is an RBI rule for payment aggregators, not a Stripe-only hurdle. There is no clean workaround that both takes real money and tells the site the payment succeeded.

Stripe is a weak fit for this product. Domestic UPI in India still needs full merchant verification, and Stripe's India rollout has been limited. Razorpay or Cashfree is the practical UPI path.

Three usable levels:

Real UPI or card money cannot be accepted, and an order cannot be auto-confirmed from that payment, without KYC. That is an RBI rule for payment aggregators, not a Stripe-only hurdle. There is no clean workaround that both takes real money and tells the site the payment succeeded.

Stripe is a weak fit for this product. Domestic UPI in India still needs full merchant verification, and Stripe's India rollout has been limited. Razorpay or Cashfree is the practical UPI path.

Three usable levels:

1. Demo, no real money, automatic confirmation. Razorpay test mode works as soon as an account exists, before KYC. Test keys start with `rzp_test_`. A test UPI id of `success@razorpay` succeeds and `failure@razorpay` fails. Razorpay then calls our server, and only that call confirms the order. The same path is what live mode uses later.
2. Live payments, after KYC. Swap in `rzp_live_` keys. Customers pay by UPI, card, or wallet, and the webhook confirms the order. Cash on delivery can stay for pickup, with the kitchen confirming payment at the counter.
3. A personal UPI QR. Fine as a picture in a demo. The site never hears that the money arrived, so confirmation stays manual: someone watches the UPI app and marks the order paid. A customer button that says "I paid" can be pressed without paying. Do not treat a static QR as an automatic gateway.

## Hold

Payment is Razorpay test mode. Hosting, when it is deployed, is App Runner plus a private Postgres in Mumbai. Do not deploy until that is asked for again.

What is in the app now: sixteen Pune branches, delivery assigned to the closest kitchen, pickup with a manual kitchen choice, orders stored in SQLite, and confirmation only after Razorpay verifies the payment. Pickup can also be pay-at-counter. The kitchen board is `kitchen.html`. Test keys live in `rzp-key.csv`, which git ignores.
