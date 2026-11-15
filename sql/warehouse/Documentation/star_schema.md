
erDiagram
    DIM_CUSTOMER ||--o{ FACT_SALES : "customer_key"
    DIM_PRODUCT ||--o{ FACT_SALES : "product_key"
    DIM_DATE ||--o{ FACT_SALES : "date_key"
    DIM_GEOGRAPHY ||--o{ FACT_SALES : "geography_key"
    DIM_PAYMENT_METHOD ||--o{ FACT_SALES : "payment_method_key"
    DIM_ORDER_STATUS ||--o{ FACT_SALES : "order_status_key"

    DIM_CUSTOMER {
        int customer_key PK
        bigint customer_id
    }

    DIM_PRODUCT {
        int product_key PK
        bigint product_id
        nvarchar product_name
        nvarchar product_category
    }

    DIM_DATE {
        int date_key PK
        date full_date
        int day_number
        nvarchar day_name
        int month_number
        nvarchar month_name
        int quarter_number
        int year_number
        int week_number
    }

    DIM_GEOGRAPHY {
        int geography_key PK
        nvarchar region
        nvarchar country
    }

    DIM_PAYMENT_METHOD {
        int payment_method_key PK
        nvarchar payment_method
    }

    DIM_ORDER_STATUS {
        int order_status_key PK
        nvarchar order_status
    }

    FACT_SALES {
        bigint sales_key PK
        bigint order_id
        int customer_key FK
        int product_key FK
        int date_key FK
        int geography_key FK
        int payment_method_key FK
        int order_status_key FK
        int quantity
        decimal unit_price
        decimal discount
        decimal shipping_cost
    }
