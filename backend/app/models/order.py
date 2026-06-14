from datetime import datetime

from ..extensions import db

STATUS_DRAFT = "draft"
STATUS_APPROVED = "approved"
STATUS_RECEIVED = "received"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"

STATUS_LABELS = {
    STATUS_DRAFT: "草稿",
    STATUS_APPROVED: "已审批",
    STATUS_RECEIVED: "已到货",
    STATUS_COMPLETED: "已完成",
    STATUS_CANCELLED: "已取消",
}

STATUS_TRANSITIONS = {
    STATUS_DRAFT: [STATUS_APPROVED, STATUS_CANCELLED],
    STATUS_APPROVED: [STATUS_RECEIVED, STATUS_CANCELLED],
    STATUS_RECEIVED: [STATUS_COMPLETED],
    STATUS_COMPLETED: [],
    STATUS_CANCELLED: [],
}

STATUS_NEXT_ACTIONS = {
    STATUS_DRAFT: "可审批或取消订单",
    STATUS_APPROVED: "可标记到货或取消订单",
    STATUS_RECEIVED: "可标记完成",
    STATUS_COMPLETED: "订单已完成，无法再变更状态",
    STATUS_CANCELLED: "订单已取消，无法再变更状态",
}


def can_transition(current_status, target_status):
    return target_status in STATUS_TRANSITIONS.get(current_status, [])


def get_available_transitions(current_status):
    return STATUS_TRANSITIONS.get(current_status, [])


def get_next_actions_hint(current_status):
    return STATUS_NEXT_ACTIONS.get(current_status, "未知状态")


class PurchaseOrder(db.Model):
    __tablename__ = "purchase_orders"

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(40), nullable=False, unique=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_DRAFT)
    expected_date = db.Column(db.Date, nullable=True)
    remark = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    supplier = db.relationship("Supplier", back_populates="orders")
    items = db.relationship(
        "PurchaseOrderItem", cascade="all, delete-orphan", back_populates="order"
    )

    @property
    def total_amount(self):
        return sum(item.quantity * item.unit_price for item in self.items)

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)

    def can_transition_to(self, target_status):
        return can_transition(self.status, target_status)

    def available_transitions(self):
        return get_available_transitions(self.status)

    def next_actions_hint(self):
        return get_next_actions_hint(self.status)

    def to_dict(self):
        return {
            "id": self.id,
            "orderNo": self.order_no,
            "supplierId": self.supplier_id,
            "supplierName": self.supplier.name if self.supplier else None,
            "status": self.status,
            "statusLabel": self.status_label,
            "expectedDate": self.expected_date.isoformat() if self.expected_date else None,
            "remark": self.remark,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "totalAmount": self.total_amount,
            "items": [item.to_dict() for item in self.items],
            "availableTransitions": self.available_transitions(),
            "nextActionsHint": self.next_actions_hint(),
        }


class PurchaseOrderItem(db.Model):
    __tablename__ = "purchase_order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredients.id"), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    order = db.relationship("PurchaseOrder", back_populates="items")
    ingredient = db.relationship("Ingredient")

    def to_dict(self):
        return {
            "id": self.id,
            "ingredientId": self.ingredient_id,
            "ingredientName": self.ingredient.name if self.ingredient else None,
            "unit": self.ingredient.unit if self.ingredient else None,
            "quantity": self.quantity,
            "unitPrice": self.unit_price,
            "amount": self.quantity * self.unit_price,
        }
