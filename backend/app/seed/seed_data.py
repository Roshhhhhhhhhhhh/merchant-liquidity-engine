import datetime
import json
from decimal import Decimal
from sqlalchemy.orm import Session
from app.database.session import SessionLocal, init_db
from app.models import (
    Merchant,
    Product,
    InventoryItem,
    Customer,
    Transaction,
    Receivable,
    Payable,
    EconomicSnapshot,
    ActivityEvent,
)
from app.core.logging import logger


def seed_database(db: Session = None):
    should_close = False
    if db is None:
        init_db()
        db = SessionLocal()
        should_close = True

    try:
        logger.info("Starting seed data generation for Aarav Industrial Supplies...")

        # Clear existing data in reverse order of dependencies
        db.query(ActivityEvent).delete()
        db.query(EconomicSnapshot).delete()
        db.query(Receivable).delete()
        db.query(Payable).delete()
        db.query(Transaction).delete()
        db.query(InventoryItem).delete()
        db.query(Product).delete()
        db.query(Customer).delete()
        db.query(Merchant).delete()
        db.commit()

        now = datetime.datetime.utcnow()

        # 1. Seed Merchant
        merchant = Merchant(
            id="mch_aarav_001",
            name="Aarav Industrial Supplies Pvt Ltd",
            trade_name="Aarav Industrial Supplies",
            gst_number="27AAACA1234F1Z8",
            industry="B2B Flow Control & Industrial Hardware",
            address="Plot 42, MIDC Bhosari Industrial Area, Pune, Maharashtra 411026",
            base_currency="INR",
            created_at=now - datetime.timedelta(days=365),
            updated_at=now,
        )
        db.add(merchant)
        db.commit()

        # 2. Seed Products
        products_data = [
            ("prod_01", "VAL-GS-004", "Cast Steel Gate Valve 4\" ANSI 150#", "Valves", "units", Decimal("4200.00"), Decimal("6100.00"), 15),
            ("prod_02", "VAL-SS-002", "Forged SS316 Ball Valve 2\" 1000 WOG", "Valves", "units", Decimal("2800.00"), Decimal("4150.00"), 20),
            ("prod_03", "VAL-CK-006", "Dual Plate Check Valve 6\" Cast Iron", "Valves", "units", Decimal("5600.00"), Decimal("7900.00"), 10),
            ("prod_04", "ACT-PN-090", "Pneumatic Rotary Actuator 90-Deg Double Acting", "Actuators", "units", Decimal("14500.00"), Decimal("21000.00"), 6),
            ("prod_05", "ACT-EH-100", "Electro-Hydraulic Heavy Duty Actuator Unit", "Actuators", "units", Decimal("32000.00"), Decimal("46500.00"), 4),
            ("prod_06", "PIP-SS-050", "Seamless SS316 Schedule 40 Pipe 50mm x 6m", "Piping", "lengths", Decimal("8400.00"), Decimal("11800.00"), 25),
            ("prod_07", "PIP-CS-100", "Carbon Steel Seamless Pipe 100mm x 6m", "Piping", "lengths", Decimal("5200.00"), Decimal("7400.00"), 30),
            ("prod_08", "FLG-WN-004", "Forged Carbon Steel Weld Neck Flange 4\" Class 300", "Flanges", "units", Decimal("1650.00"), Decimal("2450.00"), 40),
            ("prod_09", "FLG-BL-006", "SS304 Blind Flange 6\" Class 150", "Flanges", "units", Decimal("2400.00"), Decimal("3500.00"), 25),
            ("prod_10", "FAS-B7-024", "High-Tensile B7 Stud Bolts & 2H Nuts M24 Set", "Fasteners", "sets", Decimal("180.00"), Decimal("290.00"), 100),
            ("prod_11", "FAS-SS-016", "SS304 Hex Cap Screws M16 Box of 50", "Fasteners", "boxes", Decimal("950.00"), Decimal("1420.00"), 30),
            ("prod_12", "GSK-SP-004", "Spiral Wound SS316 Graphite Gasket 4\"", "Gaskets", "units", Decimal("320.00"), Decimal("520.00"), 50),
            ("prod_13", "GSK-PT-006", "Expanded PTFE Universal Sheet Gasket 6\"", "Gaskets", "units", Decimal("480.00"), Decimal("780.00"), 40),
            ("prod_14", "SEN-FL-003", "Digital Magnetic Flow Meter Transmitter 3\"", "Sensors", "units", Decimal("18500.00"), Decimal("27000.00"), 5),
        ]

        products_dict = {}
        for p_id, sku, name, cat, unit, cost, price, min_stock in products_data:
            p = Product(
                id=p_id,
                merchant_id=merchant.id,
                sku=sku,
                name=name,
                category=cat,
                unit=unit,
                unit_cost=cost,
                current_price=price,
                min_stock_threshold=min_stock,
                created_at=now - datetime.timedelta(days=180),
                updated_at=now,
            )
            db.add(p)
            products_dict[p_id] = p
        db.commit()

        # 3. Seed Inventory Items
        inventory_data = [
            ("inv_01", "prod_01", 52, 8, 24, "LOT-2026-V01", "Aisle 1 - Bay A", "Healthy", "Stable"),
            ("inv_02", "prod_02", 78, 12, 18, "LOT-2026-V02", "Aisle 1 - Bay B", "Healthy", "Increasing"),
            ("inv_03", "prod_03", 28, 4, 38, "LOT-2026-V03", "Aisle 1 - Bay C", "Watch", "Stable"),
            ("inv_04", "prod_04", 16, 2, 54, "LOT-2026-A01", "Aisle 2 - High Value", "Aging", "Softening"),
            ("inv_05", "prod_06", 45, 10, 22, "LOT-2026-P01", "Pipe Yard - Rack 1", "Healthy", "Stable"),
            ("inv_06", "prod_07", 62, 15, 34, "LOT-2026-P02", "Pipe Yard - Rack 2", "Watch", "Stable"),
            ("inv_07", "prod_08", 120, 20, 26, "LOT-2026-F01", "Aisle 3 - Bay A", "Healthy", "Increasing"),
            ("inv_08", "prod_09", 42, 5, 62, "LOT-2026-F02", "Aisle 3 - Bay B", "Aging", "Softening"),
            ("inv_09", "prod_10", 420, 50, 15, "LOT-2026-B01", "Fastener Bins 1-4", "Healthy", "Increasing"),
            ("inv_10", "prod_11", 55, 6, 28, "LOT-2026-B02", "Fastener Bins 5-8", "Healthy", "Stable"),
            ("inv_11", "prod_12", 180, 25, 20, "LOT-2026-G01", "Gasket Rack A", "Healthy", "Stable"),
            ("inv_12", "prod_13", 95, 10, 32, "LOT-2026-G02", "Gasket Rack B", "Watch", "Stable"),
            ("inv_13", "prod_05", 9, 1, 78, "LOT-2026-A02", "Secure Vault 2", "Critical", "Declining"),
            ("inv_14", "prod_14", 8, 2, 65, "LOT-2026-S01", "Electronics Cage", "Aging", "Softening"),
        ]

        for inv_id, p_id, avail, rsv, days_stk, batch, loc, status, dem in inventory_data:
            inv = InventoryItem(
                id=inv_id,
                product_id=p_id,
                merchant_id=merchant.id,
                available_quantity=avail,
                reserved_quantity=rsv,
                days_in_stock=days_stk,
                batch_number=batch,
                location=loc,
                status=status,
                demand_trend=dem,
                last_restocked_at=now - datetime.timedelta(days=days_stk),
                updated_at=now,
            )
            db.add(inv)
        db.commit()

        # 4. Seed Customers
        customers_data = [
            ("cust_01", "L&T Heavy Engineering Ltd", "Vikram Malhotra", "vikram.m@lnthe.example.com", "+91 98201 44551", "27AAACL1234F1Z1", Decimal("1500000.00"), 45, Decimal("1850000.00"), "Enterprise", 88),
            ("cust_02", "Bharat Heavy Fabricators", "Sanjay Rao", "sanjay@bhfabricators.example.com", "+91 98112 33442", "27AABCB5678G1Z2", Decimal("1200000.00"), 30, Decimal("1420000.00"), "Enterprise", 78),
            ("cust_03", "Gujarat Petrochem Infra", "Ketan Patel", "kpatel@gujpetro.example.com", "+91 98791 22331", "24AABCG9012H1Z3", Decimal("800000.00"), 30, Decimal("980000.00"), "Tier-1", 82),
            ("cust_04", "Mahindra Industrial Infra", "Rohit Deshmukh", "deshmukh.r@mahindrainfra.example.com", "+91 98220 55663", "27AAACM3456J1Z4", Decimal("1000000.00"), 45, Decimal("1240000.00"), "Enterprise", 85),
            ("cust_05", "Deccan Refineries & Chemicals", "Arjun Reddy", "areddy@deccanrefine.example.com", "+91 98490 77884", "36AABCD7890K1Z5", Decimal("600000.00"), 30, Decimal("640000.00"), "Tier-1", 72),
            ("cust_06", "Pune Thermal Power Works", "Mahesh Kulkarni", "mkulkarni@punepower.example.com", "+91 98231 88995", "27AAACP2345L1Z6", Decimal("500000.00"), 30, Decimal("510000.00"), "Tier-1", 68),
            ("cust_07", "Apex Fluid Automation Systems", "Naveen Singhal", "naveen@apexfluid.example.com", "+91 98100 99006", "07AABCA6789M1Z7", Decimal("300000.00"), 15, Decimal("390000.00"), "Standard", 92),
            ("cust_08", "Vanguard Process Equipments", "Amitabh Sen", "asen@vanguardpe.example.com", "+91 98300 11227", "19AABCV0123N1Z8", Decimal("400000.00"), 30, Decimal("430000.00"), "Standard", 75),
        ]

        customers_dict = {}
        for c_id, comp, name, email, phone, gstin, cred_lim, terms, rev, tier, score in customers_data:
            cust = Customer(
                id=c_id,
                merchant_id=merchant.id,
                name=name,
                company_name=comp,
                email=email,
                phone=phone,
                gstin=gstin,
                credit_limit=cred_lim,
                credit_terms_days=terms,
                total_revenue=rev,
                customer_tier=tier,
                payment_score=score,
                created_at=now - datetime.timedelta(days=300),
                updated_at=now,
            )
            db.add(cust)
            customers_dict[c_id] = cust
        db.commit()

        # 5. Seed Receivables
        # Total Outstanding: ₹18,40,000 | Overdue: ₹5,70,000 | Due this week: ₹7,30,000
        receivables_data = [
            ("rec_01", "cust_06", "INV-2026-0842", Decimal("240000.00"), Decimal("0.00"), Decimal("240000.00"), 48, -18, "Severely Overdue", "Payment delayed due to state treasury audit. Escalated to billing director."),
            ("rec_02", "cust_05", "INV-2026-0855", Decimal("330000.00"), Decimal("0.00"), Decimal("330000.00"), 35, -5, "Overdue", "Pending finance controller approval. Follow-up promised by Thursday."),
            ("rec_03", "cust_01", "INV-2026-0889", Decimal("420000.00"), Decimal("0.00"), Decimal("420000.00"), 37, 8, "Current", "Scheduled in L&T regular supplier payment cycle next week."),
            ("rec_04", "cust_02", "INV-2026-0895", Decimal("310000.00"), Decimal("0.00"), Decimal("310000.00"), 26, 4, "Due Soon", "Invoice approved by QA; payment queued in corporate banking."),
            ("rec_05", "cust_03", "INV-2026-0902", Decimal("280000.00"), Decimal("0.00"), Decimal("280000.00"), 14, 16, "Current", "Fresh dispatch for Dahej expansion project."),
            ("rec_06", "cust_04", "INV-2026-0914", Decimal("150000.00"), Decimal("0.00"), Decimal("150000.00"), 10, 35, "Current", "Standard 45-day commercial terms."),
            ("rec_07", "cust_07", "INV-2026-0920", Decimal("60000.00"), Decimal("0.00"), Decimal("60000.00"), 8, 7, "Due Soon", "Apex automation actuator lot delivery."),
            ("rec_08", "cust_08", "INV-2026-0928", Decimal("50000.00"), Decimal("0.00"), Decimal("50000.00"), 4, 26, "Current", "Fastener & flange replenishment order."),
        ]

        for r_id, c_id, inv_num, amt, paid, bal, days_ago, days_to_due, status, note in receivables_data:
            rec = Receivable(
                id=r_id,
                merchant_id=merchant.id,
                customer_id=c_id,
                invoice_number=inv_num,
                amount=amt,
                paid_amount=paid,
                balance_due=bal,
                issue_date=now - datetime.timedelta(days=days_ago),
                due_date=now + datetime.timedelta(days=days_to_due),
                status=status,
                days_overdue=max(0, -days_to_due) if status in ("Overdue", "Severely Overdue") else 0,
                notes=note,
                created_at=now - datetime.timedelta(days=days_ago),
                updated_at=now,
            )
            db.add(rec)
        db.commit()

        # 6. Seed Payables (Total: ₹12,60,000 | Due in 12d: ₹3,50,000)
        payables_data = [
            ("pay_01", "Mahasagar Steel Castings Ltd", "BILL-MSC-4412", Decimal("185000.00"), Decimal("0.00"), Decimal("185000.00"), 24, 6, "Raw Materials", "Pending", "Critical", "Raw valve casting supply batch; priority to maintain foundry discount"),
            ("pay_02", "Apex Precision Machining Works", "BILL-APM-1980", Decimal("165000.00"), Decimal("0.00"), Decimal("165000.00"), 19, 11, "Machining", "Pending", "High", "CNC machining for actuator bodies & spindles"),
            ("pay_03", "Jindal Seamless Tubular Pipes", "BILL-JST-8821", Decimal("420000.00"), Decimal("0.00"), Decimal("420000.00"), 12, 18, "Raw Materials", "Scheduled", "Medium", "Schedule 40 pipe consignment for Q3 inventory"),
            ("pay_04", "Techno-Seal Gasket Industries", "BILL-TSG-0914", Decimal("90000.00"), Decimal("0.00"), Decimal("90000.00"), 15, 15, "Raw Materials", "Scheduled", "Medium", "PTFE and graphite gasket lot"),
            ("pay_05", "FastTrack Freight & Logistics", "BILL-FTF-3211", Decimal("75000.00"), Decimal("0.00"), Decimal("75000.00"), 8, 22, "Logistics", "Pending", "Medium", "Interstate transport to Dahej & Hazira sites"),
            ("pay_06", "MIDC Industrial Power & Water", "BILL-MIDC-0826", Decimal("45000.00"), Decimal("0.00"), Decimal("45000.00"), 5, 25, "Utilities", "Pending", "Medium", "Monthly utility bill"),
            ("pay_07", "Kalyani Forging Mills Pvt Ltd", "BILL-KFM-6712", Decimal("280000.00"), Decimal("0.00"), Decimal("280000.00"), 2, 28, "Raw Materials", "Pending", "High", "Weld neck flange blanks"),
        ]

        for p_id, vendor, inv_num, amt, paid, bal, days_ago, days_to_due, cat, status, pri, note in payables_data:
            pay = Payable(
                id=p_id,
                merchant_id=merchant.id,
                vendor_name=vendor,
                invoice_number=inv_num,
                amount=amt,
                paid_amount=paid,
                balance_due=bal,
                issue_date=now - datetime.timedelta(days=days_ago),
                due_date=now + datetime.timedelta(days=days_to_due),
                category=cat,
                status=status,
                priority=pri,
                notes=note,
                created_at=now - datetime.timedelta(days=days_ago),
                updated_at=now,
            )
            db.add(pay)
        db.commit()

        # 7. Seed Transactions (24 recent transactions across 30 days)
        tx_specs = [
            ("tx_01", "cust_01", "prod_01", 30, Decimal("6100.00"), 2, "Captured", "Settled", "Razorpay Virtual Account", "Direct B2B"),
            ("tx_02", "cust_02", "prod_02", 40, Decimal("4150.00"), 4, "Captured", "Settled", "NEFT/RTGS", "PO Fulfillment"),
            ("tx_03", "cust_03", "prod_06", 15, Decimal("11800.00"), 6, "Captured", "Settled", "NEFT/RTGS", "Direct B2B"),
            ("tx_04", "cust_04", "prod_08", 50, Decimal("2450.00"), 8, "Captured", "Settled", "Corporate Card", "Distributor Portal"),
            ("tx_05", "cust_07", "prod_04", 4, Decimal("21000.00"), 9, "Captured", "Settled", "UPI Autopay", "Direct B2B"),
            ("tx_06", "cust_05", "prod_07", 20, Decimal("7400.00"), 11, "Captured", "Settled", "NEFT/RTGS", "PO Fulfillment"),
            ("tx_07", "cust_08", "prod_10", 200, Decimal("290.00"), 13, "Captured", "Settled", "NEFT/RTGS", "Direct B2B"),
            ("tx_08", "cust_01", "prod_03", 8, Decimal("7900.00"), 15, "Captured", "Settled", "Razorpay Virtual Account", "Direct B2B"),
            ("tx_09", "cust_02", "prod_11", 20, Decimal("1420.00"), 16, "Captured", "Settled", "NEFT/RTGS", "PO Fulfillment"),
            ("tx_10", "cust_03", "prod_12", 100, Decimal("520.00"), 18, "Captured", "Settled", "NEFT/RTGS", "Distributor Portal"),
            ("tx_11", "cust_04", "prod_01", 20, Decimal("6100.00"), 20, "Captured", "Settled", "Corporate Card", "Direct B2B"),
            ("tx_12", "cust_06", "prod_09", 15, Decimal("3500.00"), 22, "Captured", "Settled", "NEFT/RTGS", "PO Fulfillment"),
            ("tx_13", "cust_07", "prod_13", 50, Decimal("780.00"), 24, "Captured", "Settled", "UPI Autopay", "Direct B2B"),
            ("tx_14", "cust_08", "prod_02", 25, Decimal("4150.00"), 25, "Captured", "Settled", "NEFT/RTGS", "Direct B2B"),
            ("tx_15", "cust_01", "prod_06", 12, Decimal("11800.00"), 27, "Captured", "Settled", "Razorpay Virtual Account", "PO Fulfillment"),
            ("tx_16", "cust_02", "prod_08", 60, Decimal("2450.00"), 28, "Captured", "Settled", "NEFT/RTGS", "Direct B2B"),
            ("tx_17", "cust_03", "prod_04", 3, Decimal("21000.00"), 29, "Captured", "Settled", "NEFT/RTGS", "Distributor Portal"),
            ("tx_18", "cust_05", "prod_01", 15, Decimal("6100.00"), 1, "Captured", "In Transit", "NEFT/RTGS", "PO Fulfillment"),
            ("tx_19", "cust_04", "prod_10", 150, Decimal("290.00"), 1, "Captured", "In Transit", "Corporate Card", "Direct B2B"),
            ("tx_20", "cust_07", "prod_14", 2, Decimal("27000.00"), 0, "Captured", "Pending", "UPI Autopay", "Direct B2B"),
        ]

        for tx_id, c_id, p_id, qty, u_price, days_ago, p_stat, s_stat, p_meth, chn in tx_specs:
            prod = products_dict[p_id]
            cost_val = Decimal(qty) * Decimal(str(prod.unit_cost))
            gross_val = Decimal(qty) * u_price
            margin_pct = ((gross_val - cost_val) / gross_val * Decimal(100)) if gross_val > 0 else Decimal(0)

            tx = Transaction(
                id=tx_id,
                merchant_id=merchant.id,
                customer_id=c_id,
                product_id=p_id,
                reference_id=f"TXN-2026-{1000 + int(tx_id.split('_')[1]):05d}",
                quantity=qty,
                unit_price=u_price,
                gross_value=gross_val,
                cost_value=cost_val,
                net_margin_pct=round(margin_pct, 2),
                payment_status=p_stat,
                settlement_status=s_stat,
                payment_method=p_meth,
                channel=chn,
                created_at=now - datetime.timedelta(days=days_ago, hours=3, minutes=15),
            )
            db.add(tx)
        db.commit()

        # 8. Seed 30-Day Economic Snapshots
        # Demonstrates a realistic MSME trajectory:
        # Starting Day -29: Cash ~₹6.80L, Payables ~₹14.20L, Receivables ~₹15.50L, Inventory ~₹33.50L
        # Mid-month: Paid major supplier tranche (-₹3.80L), collections delayed by Pune Thermal & Deccan,
        # Ending Day 0: Cash at ₹4.85L (mild stress, 24-day runway), Receivables at ₹18.40L, Payables at ₹12.60L, Inventory at ₹34.20L.
        snapshots_data = [
            (-29, Decimal("680000.00"), Decimal("1550000.00"), Decimal("1420000.00"), Decimal("3350000.00"), Decimal("720000.00"), Decimal("28.8"), 33, Decimal("1.57"), Decimal("3.93"), Decimal("4160000.00"), 40, 36, 56, 60, 42, "Month Opening Equilibrium"),
            (-27, Decimal("695000.00"), Decimal("1580000.00"), Decimal("1410000.00"), Decimal("3370000.00"), Decimal("720000.00"), Decimal("28.8"), 34, Decimal("1.61"), Decimal("4.00"), Decimal("4235000.00"), 40, 36, 56, 60, 40, None),
            (-25, Decimal("740000.00"), Decimal("1520000.00"), Decimal("1390000.00"), Decimal("3360000.00"), Decimal("730000.00"), Decimal("28.7"), 36, Decimal("1.63"), Decimal("4.04"), Decimal("4230000.00"), 39, 36, 57, 60, 38, "L&T Milestone Settlement (+₹1.80L)"),
            (-23, Decimal("710000.00"), Decimal("1590000.00"), Decimal("1380000.00"), Decimal("3380000.00"), Decimal("740000.00"), Decimal("28.6"), 35, Decimal("1.67"), Decimal("4.12"), Decimal("4300000.00"), 40, 36, 57, 61, 40, None),
            (-21, Decimal("660000.00"), Decimal("1650000.00"), Decimal("1370000.00"), Decimal("3390000.00"), Decimal("760000.00"), Decimal("28.6"), 32, Decimal("1.69"), Decimal("4.16"), Decimal("4330000.00"), 41, 35, 57, 63, 44, None),
            (-19, Decimal("590000.00"), Decimal("1720000.00"), Decimal("1580000.00"), Decimal("3520000.00"), Decimal("780000.00"), Decimal("28.5"), 29, Decimal("1.46"), Decimal("3.69"), Decimal("4250000.00"), 42, 35, 58, 65, 52, "Raw Material Inbound Batch (+₹2.10L Payables)"),
            (-17, Decimal("540000.00"), Decimal("1740000.00"), Decimal("1560000.00"), Decimal("3510000.00"), Decimal("790000.00"), Decimal("28.5"), 26, Decimal("1.46"), Decimal("3.71"), Decimal("4230000.00"), 42, 35, 58, 65, 55, None),
            (-15, Decimal("510000.00"), Decimal("1790000.00"), Decimal("1520000.00"), Decimal("3490000.00"), Decimal("810000.00"), Decimal("28.4"), 25, Decimal("1.51"), Decimal("3.81"), Decimal("4270000.00"), 43, 35, 58, 66, 58, "Tax & GST Outflow (-₹1.20L)"),
            (-13, Decimal("530000.00"), Decimal("1780000.00"), Decimal("1480000.00"), Decimal("3470000.00"), Decimal("820000.00"), Decimal("28.4"), 26, Decimal("1.56"), Decimal("3.91"), Decimal("4300000.00"), 42, 35, 58, 65, 56, None),
            (-11, Decimal("560000.00"), Decimal("1760000.00"), Decimal("1440000.00"), Decimal("3460000.00"), Decimal("830000.00"), Decimal("28.4"), 27, Decimal("1.61"), Decimal("4.01"), Decimal("4340000.00"), 42, 35, 58, 65, 54, None),
            (-9, Decimal("520000.00"), Decimal("1810000.00"), Decimal("1390000.00"), Decimal("3450000.00"), Decimal("850000.00"), Decimal("28.4"), 25, Decimal("1.68"), Decimal("4.16"), Decimal("4390000.00"), 43, 35, 58, 66, 60, "Deccan Refineries Overdue Trigger (>30d)"),
            (-7, Decimal("490000.00"), Decimal("1830000.00"), Decimal("1350000.00"), Decimal("3440000.00"), Decimal("860000.00"), Decimal("28.4"), 24, Decimal("1.72"), Decimal("4.27"), Decimal("4410000.00"), 43, 35, 58, 66, 64, None),
            (-5, Decimal("475000.00"), Decimal("1850000.00"), Decimal("1310000.00"), Decimal("3430000.00"), Decimal("870000.00"), Decimal("28.4"), 23, Decimal("1.77"), Decimal("4.39"), Decimal("4445000.00"), 43, 35, 58, 66, 66, "Supplier Payment: Mahasagar Steel Part 1"),
            (-3, Decimal("495000.00"), Decimal("1820000.00"), Decimal("1280000.00"), Decimal("3420000.00"), Decimal("880000.00"), Decimal("28.4"), 24, Decimal("1.81"), Decimal("4.48"), Decimal("4455000.00"), 42, 35, 58, 65, 65, None),
            (-1, Decimal("480000.00"), Decimal("1840000.00"), Decimal("1260000.00"), Decimal("3420000.00"), Decimal("890000.00"), Decimal("28.4"), 23, Decimal("1.84"), Decimal("4.56"), Decimal("4480000.00"), 42, 35, 58, 65, 68, "Pune Thermal Power Audit Delay Flagged"),
            (0, Decimal("485000.00"), Decimal("1840000.00"), Decimal("1260000.00"), Decimal("3420000.00"), Decimal("890000.00"), Decimal("28.4"), 24, Decimal("1.85"), Decimal("4.56"), Decimal("4485000.00"), 42, 35, 58, 65, 68, "Current Operating Snapshot"),
        ]

        for days_ago, cash, rec_val, pay_val, inv_val, ag_val, margin, r_days, q_rat, c_rat, wc, dso, dpo, dio, ccc, stress, evt in snapshots_data:
            snap = EconomicSnapshot(
                id=f"snap_{abs(days_ago):02d}",
                merchant_id=merchant.id,
                snapshot_date=now + datetime.timedelta(days=days_ago),
                cash_balance=cash,
                total_receivables=rec_val,
                total_payables=pay_val,
                inventory_value=inv_val,
                aging_inventory_value=ag_val,
                gross_margin_pct=margin,
                cash_runway_days=r_days,
                quick_ratio=q_rat,
                current_ratio=c_rat,
                working_capital=wc,
                dso_days=dso,
                dpo_days=dpo,
                dio_days=dio,
                cash_conversion_cycle=ccc,
                liquidity_stress_score=stress,
                event_marker=evt,
                notes=f"Daily closing balance. Liquidity stress level: {stress}/100",
                created_at=now + datetime.timedelta(days=days_ago),
            )
            db.add(snap)
        db.commit()

        # 9. Seed Activity Events
        activities_data = [
            ("act_01", "Liquidity", "Daily Liquidity Snapshot Generated", "Cash runway evaluated at 24 days. Working capital at ₹44.85L with liquidity stress index at 68/100 (Warning).", "Medium", 0, json.dumps({"cash": 485000, "runway_days": 24, "stress_score": 68})),
            ("act_02", "Receivables", "Receivable Overdue Alert - Pune Thermal Power", "Invoice INV-2026-0842 (₹2.40L) is now 18 days overdue. Collections delay attributed to state audit.", "High", 1, json.dumps({"invoice": "INV-2026-0842", "amount": 240000, "customer": "Pune Thermal Power Works"})),
            ("act_03", "Inventory", "Inventory Aging Threshold Crossed", "Electro-Hydraulic Actuator Unit (SKU: ACT-EH-100) exceeded 75 days in stock. Capital locked: ₹2.88L.", "Medium", 2, json.dumps({"sku": "ACT-EH-100", "days_in_stock": 78, "value_locked": 288000})),
            ("act_04", "Payables", "Upcoming Supplier Commitment", "Mahasagar Steel Castings invoice BILL-MSC-4412 (₹1.85L) due in 6 days. Scheduled for payment processing.", "Medium", 3, json.dumps({"vendor": "Mahasagar Steel Castings Ltd", "amount": 185000, "due_days": 6})),
            ("act_05", "Transactions", "High-Value Transaction Recorded", "L&T Heavy Engineering order fulfilled for 30x Cast Steel Gate Valves. Gross value: ₹1.83L at 31.1% margin.", "Info", 4, json.dumps({"reference": "TXN-2026-01001", "gross": 183000, "customer": "L&T Heavy Engineering Ltd"})),
            ("act_06", "Receivables", "Receivable Due Soon - Bharat Heavy Fabricators", "Invoice INV-2026-0895 (₹3.10L) due in 4 days. Payment approval confirmed with client AP team.", "Info", 5, json.dumps({"invoice": "INV-2026-0895", "amount": 310000, "customer": "Bharat Heavy Fabricators"})),
            ("act_07", "Demand", "Demand Velocity Shift Detected", "MoM order volume in Valves category softened by 4.2% across Western industrial corridor.", "Low", 6, json.dumps({"category": "Valves", "mom_shift_pct": -4.2})),
            ("act_08", "Liquidity", "Working Capital Rebalance Complete", "Settled batch raw material supply invoices totaling ₹3.80L from operational cash reserves.", "Info", 8, json.dumps({"settlement_amount": 380000})),
            ("act_09", "Receivables", "Overdue Escalation - Deccan Refineries", "Invoice INV-2026-0855 (₹3.30L) crossed 30-day term. Reminder dispatch generated.", "High", 9, json.dumps({"invoice": "INV-2026-0855", "amount": 330000, "customer": "Deccan Refineries & Chemicals"})),
            ("act_10", "Inventory", "Fastener Stock Reorder Level Reached", "High-Tensile B7 Stud Bolts (SKU: FAS-B7-024) stock depleted to 420 sets following bulk dispatch.", "Low", 11, json.dumps({"sku": "FAS-B7-024", "current_stock": 420})),
        ]

        for act_id, cat, title, desc, sev, days_ago, meta in activities_data:
            act = ActivityEvent(
                id=act_id,
                merchant_id=merchant.id,
                event_type=f"{cat.lower()}.event",
                category=cat,
                title=title,
                description=desc,
                severity=sev,
                metadata_json=meta,
                created_at=now - datetime.timedelta(days=days_ago, hours=2),
            )
            db.add(act)
        db.commit()

        logger.info("Database successfully seeded with realistic MSME operating data!")

    except Exception as e:
        logger.error(f"Error seeding database: {e}", exc_info=True)
        db.rollback()
        raise e
    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    seed_database()
