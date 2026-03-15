from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# PRODUCTS (FIXED ORDER FOR ASSIGNMENT)
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 199, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]

feedback = []

# STORAGE
cart = []
orders = []
order_counter = 1


class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)


class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)


class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem]


class Product(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool


class Checkout(BaseModel):
    customer_name: str
    delivery_address: str


# GET ALL PRODUCTS
@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}


# CATEGORY FILTER
@app.get("/products/category/{category_name}")
def get_category(category_name: str):

    filtered = [p for p in products if p["category"].lower() == category_name.lower()]

    if not filtered:
        raise HTTPException(status_code=404, detail="No products found in this category")

    return filtered


# IN STOCK PRODUCTS
@app.get("/products/instock")
def get_instock_products():

    instock_products = [p for p in products if p["in_stock"]]

    return {
        "in_stock_products": instock_products,
        "count": len(instock_products)
    }


# SEARCH PRODUCTS
@app.get("/products/search/{keyword}")
def search_products(keyword: str):

    result = [p for p in products if keyword.lower() in p["name"].lower()]

    if not result:
        return {"message": "No products matched your search"}

    return {
        "keyword": keyword,
        "matched_products": result,
        "count": len(result)
    }


# PRODUCT PRICE
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):

    for product in products:
        if product["id"] == product_id:
            return {
                "name": product["name"],
                "price": product["price"]
            }

    raise HTTPException(status_code=404, detail="Product not found")


# FEEDBACK
@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):

    feedback.append(data)

    return {
        "message": "Feedback submitted successfully",
        "feedback": data,
        "total_feedback": len(feedback)
    }


# ADD PRODUCT
@app.post("/products", status_code=201)
def add_product(product: Product):

    for p in products:
        if p["name"].lower() == product.name.lower():
            raise HTTPException(status_code=400, detail="Product with this name already exists")

    new_id = max(p["id"] for p in products) + 1

    new_product = {
        "id": new_id,
        "name": product.name,
        "price": product.price,
        "category": product.category,
        "in_stock": product.in_stock
    }

    products.append(new_product)

    return {
        "message": "Product added",
        "product": new_product
    }


# ---------------------------
# CART SYSTEM (ASSIGNMENT)
# ---------------------------

# ADD TO CART
@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int = Query(1, ge=1)):

    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail=f"{product['name']} is out of stock")

    existing = next((item for item in cart if item["product_id"] == product_id), None)

    if existing:
        existing["quantity"] += quantity
        existing["subtotal"] = existing["quantity"] * existing["unit_price"]

        return {
            "message": "Cart updated",
            "cart_item": existing
        }

    subtotal = product["price"] * quantity

    cart_item = {
        "product_id": product["id"],
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": subtotal
    }

    cart.append(cart_item)

    return {
        "message": "Added to cart",
        "cart_item": cart_item
    }


# VIEW CART
@app.get("/cart")
def view_cart():

    if not cart:
        return {
            "message": "Cart is empty",
            "items": [],
            "item_count": 0,
            "grand_total": 0
        }

    grand_total = sum(item["subtotal"] for item in cart)

    return {
        "items": cart,
        "item_count": len(cart),
        "grand_total": grand_total
    }


# REMOVE ITEM FROM CART
@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):

    for item in cart:
        if item["product_id"] == product_id:
            cart.remove(item)

            return {
                "message": f"{item['product_name']} removed from cart"
            }

    raise HTTPException(status_code=404, detail="Item not found in cart")


# CHECKOUT
@app.post("/cart/checkout")
def checkout(data: Checkout):

    global order_counter

    if not cart:
        raise HTTPException(status_code=400, detail="CART_EMPTY")

    placed_orders = []

    for item in cart:

        order = {
            "order_id": order_counter,
            "customer_name": data.customer_name,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "subtotal": item["subtotal"],
            "delivery_address": data.delivery_address
        }

        orders.append(order)
        placed_orders.append(order)

        order_counter += 1

    grand_total = sum(item["subtotal"] for item in cart)

    cart.clear()

    return {
        "orders_placed": placed_orders,
        "grand_total": grand_total
    }


# GET ORDERS
@app.get("/orders")
def get_orders():

    return {
        "orders": orders,
        "total_orders": len(orders)
    }