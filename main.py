from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
import uvicorn

app = FastAPI()

# A mock database for orders
orders = []

@app.post("/api/checkout")
async def checkout(request: Request):
    data = await request.json()
    order_id = f"GC{100000 + len(orders) * 13}"
    orders.append({
        "order_id": order_id,
        "details": data
    })
    return {"success": True, "order_id": order_id, "message": "Order placed successfully!"}

@app.get("/api/orders")
async def get_orders():
    return {"orders": orders}

# Serve static files (assets)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Serve HTML files
@app.get("/")
@app.get("/index.html")
async def serve_index():
    with open("index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/menu.html")
async def serve_menu():
    with open("menu.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/checkout.html")
async def serve_checkout():
    with open("checkout.html", "r") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
