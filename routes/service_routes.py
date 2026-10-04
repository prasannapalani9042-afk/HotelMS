from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, FoodItem, Order

service_bp = Blueprint("service", __name__, url_prefix="/services")


@service_bp.route("/menu")
@login_required
def menu():
    items = FoodItem.query.all()
    return render_template("services/menu.html", items=items)


@service_bp.route("/order", methods=["POST"])
@login_required
def place_order():
    item_ids = request.form.getlist("item_id")
    quantities = request.form.getlist("quantity")

    order_lines = []
    total = 0.0
    for item_id, qty in zip(item_ids, quantities):
        qty = int(qty)
        if qty <= 0:
            continue
        item = FoodItem.query.get(int(item_id))
        if item:
            order_lines.append(f"{item.name} x{qty}")
            total += item.price * qty

    if not order_lines:
        flash("Select at least one item.", "error")
        return redirect(url_for("service.menu"))

    order = Order(guest_id=current_user.id, items=", ".join(order_lines), total_bill=total)
    db.session.add(order)
    db.session.commit()
    flash("Order placed!", "success")
    return redirect(url_for("service.my_orders"))


@service_bp.route("/my-orders")
@login_required
def my_orders():
    orders = Order.query.filter_by(guest_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("services/my_orders.html", orders=orders)


@service_bp.route("/update-status/<int:order_id>", methods=["POST"])
@login_required
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    if current_user.role not in ("admin", "staff"):
        flash("Only hotel staff can update order status.", "error")
        return redirect(url_for("service.my_orders"))
    new_status = request.form.get("status", "placed")
    if new_status not in ("placed", "preparing", "delivered"):
        flash("Invalid order status.", "error")
        return redirect(url_for("service.my_orders"))
    order.status = new_status
    db.session.commit()
    flash("Order status updated.", "success")
    return redirect(url_for("service.my_orders"))
