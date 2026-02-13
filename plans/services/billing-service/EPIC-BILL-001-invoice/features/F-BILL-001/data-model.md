# Data Model: F-BILL-001

## Entity: Invoice

- invoice_id: string
- order_id: string
- customer_id: string
- amount_total: number
- currency: string
- created_at: string (ISO8601)
- line_items: array

## Entity: LineItem

- sku: string
- quantity: integer (>=1)
- unit_price: number (>=0)
- line_total: number (>=0)

## Validation Rules

- amount_total は line_total 合計と一致
- currency は 3 文字英字
