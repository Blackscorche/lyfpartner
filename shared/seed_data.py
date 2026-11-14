"""Seed data for 5 Nigerian demo customers, varied balances, and beneficiaries."""
import json
from datetime import datetime
from sqlalchemy import select
from shared.database import async_session_maker, CustomerModel, AccountModel, BeneficiaryModel, TransactionModel, init_db
from shared.security import hash_pin

DEMO_CUSTOMERS = [
    {
        "customer_id": "cust_aminu_001",
        "phone_number": "+2348000000001",
        "full_name": "Aminu Bello Kano",
        "bvn": "22211133344",
        "nin": "12345678901",
        "preferred_language": "ha",
        "pin": "1234",
        "caregiver_phone": "+2348009990001",
        "account_number": "0123456789",
        "balance_kobo": 25_000_000, # 250,000 NGN
        "beneficiaries": [
            {"name": "Musa Bello", "account_number": "2045678901", "bank_name": "First Bank", "nickname": "Musa"},
            {"name": "Fatima Umar", "account_number": "3012345678", "bank_name": "GTBank", "nickname": "Fatima"},
            {"name": "Abubakar Sani", "account_number": "4098765432", "bank_name": "Zenith Bank", "nickname": "Abu"}
        ]
    },
    {
        "customer_id": "cust_ngozi_002",
        "phone_number": "+2348000000002",
        "full_name": "Ngozi Chinyere Eze",
        "bvn": "22211133355",
        "nin": "12345678902",
        "preferred_language": "ig",
        "pin": "5678",
        "caregiver_phone": "+2348009990002",
        "account_number": "0123456788",
        "balance_kobo": 8_000_000, # 80,000 NGN
        "beneficiaries": [
            {"name": "Chidi Okafor", "account_number": "2156789012", "bank_name": "Access Bank", "nickname": "Chidi"},
            {"name": "Amaka Obi", "account_number": "3123456789", "bank_name": "UBA", "nickname": "Amaka"}
        ]
    },
    {
        "customer_id": "cust_babatunde_003",
        "phone_number": "+2348000000003",
        "full_name": "Babatunde Oluwaseun Adeyemi",
        "bvn": "22211133366",
        "nin": "12345678903",
        "preferred_language": "yo",
        "pin": "4321",
        "caregiver_phone": "+2348009990003",
        "account_number": "0123456787",
        "balance_kobo": 1_500_000, # 15,000 NGN
        "beneficiaries": [
            {"name": "Folake Adeleke", "account_number": "2256789013", "bank_name": "Kuda Bank", "nickname": "Folake"},
            {"name": "Kunle Bakare", "account_number": "3223456780", "bank_name": "Stanbic IBTC", "nickname": "Kunle"}
        ]
    },
    {
        "customer_id": "cust_emeka_004",
        "phone_number": "+2348000000004",
        "full_name": "Emeka Victor Johnson",
        "bvn": "22211133377",
        "nin": "12345678904",
        "preferred_language": "en-ng",
        "pin": "9999",
        "caregiver_phone": "+2348009990004",
        "account_number": "0123456786",
        "balance_kobo": 50_000_000, # 500,000 NGN
        "beneficiaries": [
            {"name": "Blessing David", "account_number": "2356789014", "bank_name": "Zenith Bank", "nickname": "Blessing"},
            {"name": "Musa Bello", "account_number": "2045678901", "bank_name": "First Bank", "nickname": "Musa"}
        ]
    },
    {
        "customer_id": "cust_hadiza_005",
        "phone_number": "+2348000000005",
        "full_name": "Hadiza Maryam Aliyu",
        "bvn": "22211133388",
        "nin": "12345678905",
        "preferred_language": "ha",
        "pin": "1122",
        "caregiver_phone": "+2348009990005",
        "account_number": "0123456785",
        "balance_kobo": 250_000, # 2,500 NGN
        "beneficiaries": [
            {"name": "Umar Faruk", "account_number": "2456789015", "bank_name": "Jaiz Bank", "nickname": "Umar"},
            {"name": "Zainab Aliyu (Caregiver)", "account_number": "3423456781", "bank_name": "Taj Bank", "nickname": "Zainab"}
        ]
    }
]

async def seed_database():
    await init_db()
    async with async_session_maker() as session:
        for c in DEMO_CUSTOMERS:
            # Check if customer already exists
            existing = await session.execute(select(CustomerModel).where(CustomerModel.customer_id == c["customer_id"]))
            if existing.scalar_one_or_none():
                continue
            
            customer = CustomerModel(
                customer_id=c["customer_id"],
                phone_number=c["phone_number"],
                full_name=c["full_name"],
                bvn=c["bvn"],
                nin=c["nin"],
                preferred_language=c["preferred_language"],
                pin_hash=hash_pin(c["pin"]),
                voiceprint_json=json.dumps([0.15] * 128), # mock 128-d speaker embedding
                caregiver_phone=c["caregiver_phone"],
                is_locked=False,
                failed_pin_attempts=0
            )
            session.add(customer)
            
            account_id = f"acc_{c['customer_id'][5:]}"
            account = AccountModel(
                account_id=account_id,
                account_number=c["account_number"],
                customer_id=c["customer_id"],
                balance_kobo=c["balance_kobo"],
                currency="NGN",
                status="active"
            )
            session.add(account)
            
            # Initial funding transaction
            tx = TransactionModel(
                transaction_id=f"tx_init_{c['customer_id'][5:]}",
                account_id=account_id,
                type="credit",
                amount_kobo=c["balance_kobo"],
                narration="Opening balance / NIP Inward Transfer",
                reference=f"REF-INIT-{c['customer_id'][5:]}",
                balance_after_kobo=c["balance_kobo"]
            )
            session.add(tx)
            
            # Beneficiaries
            for idx, b in enumerate(c["beneficiaries"]):
                ben = BeneficiaryModel(
                    beneficiary_id=f"ben_{c['customer_id'][5:]}_{idx+1}",
                    account_id=account_id,
                    name=b["name"],
                    account_number=b["account_number"],
                    bank_name=b["bank_name"],
                    nickname=b["nickname"]
                )
                session.add(ben)
                
        await session.commit()
