from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from sqlalchemy.orm import Session
import uvicorn
import os
from utils import parse_payment_json,send_whatsapp_message
from ultramessage import send_whatsapp_ultramessage
from models import engine, Base, Customer, Feedback, PaymentPayload, SessionLocal, FeedbackResponse
from register_url import register_confirmation_url

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Check if critical environment variables are set
    required_vars = [
        'MPESA_CONSUMER_KEY', 
        'MPESA_CONSUMER_SECRET', 
        'MPESA_SHORTCODE', 
        'CONFIRMATION_URL',
        'WHATSAPP_API_TOKEN'
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"WARNING: The following environment variables are missing: {', '.join(missing_vars)}")
        print("The application will attempt to start, but some functionality may not work correctly.")
        # Don't try to register URL if credentials are missing
        if 'MPESA_CONSUMER_KEY' not in missing_vars and 'MPESA_CONSUMER_SECRET' not in missing_vars:
            try:
                response = register_confirmation_url()
                print(f"URL registration successful: {response}")
            except Exception as e:
                print(f"URL registration failed but continuing startup: {e}")
    else:
        try:
            response = register_confirmation_url()
            print(f"URL registration successful: {response}")
        except Exception as e:
            print(f"URL registration failed but continuing startup: {e}")

# Payment confirmation endpoint
@app.post("/payments-confirmation")
async def payment_confirmation(payload: PaymentPayload, background_tasks: BackgroundTasks):
    print(f"Received payment confirmation: {payload.model_dump()}")
    transaction_id, firstname, secondname, lastname, phone = parse_payment_json(payload)
    if not firstname or not phone:
        raise HTTPException(status_code=400, detail="Invalid payment message format. Required fields not found.")

    # Save the customer information in the database 
    db: Session = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.phone == phone).first()
        if not customer:
            customer = Customer(first_name=firstname, second_name=secondname, last_name=lastname, phone=phone)
            db.add(customer)
            db.commit()
            db.refresh(customer)
    except Exception as e:
        db.rollback()
        print(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store customer data")
    finally:
        db.close()

    # Trigger the WhatsApp feedback message immediately (untramessage api)
    await send_whatsapp_ultramessage(phone, firstname)

    return {"status": "Payment confirmed and feedback request sent."}


@app.post("/store-feedback")
async def store_feedback(feedback: FeedbackResponse):
    db: Session = SessionLocal()
    try:
        # Locate the customer by phone number
        customer = db.query(Customer).filter(Customer.phone == feedback.phone).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found.")
        
        new_feedback = Feedback(customer_id=customer.id, rating=feedback.rating, comments=feedback.comments)
        db.add(new_feedback)
        db.commit()
        db.refresh(new_feedback)
        return {"status": "Feedback stored successfully."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store feedback")
    finally:
        db.close()

@app.get("/check-database")
async def check_database():
    db: Session = SessionLocal()
    try:
        customers = db.query(Customer).all()
        data = []
        for customer in customers:
            feedbacks = db.query(Feedback).filter(Feedback.customer_id == customer.id).all()
            data.append({
                "customer_id": customer.id,
                "first_name": customer.first_name,
                "second_name": customer.second_name,
                "last_name": customer.last_name,
                "phone": customer.phone,
                "feedback": [
                    {
                        "feedback_id": fb.id,
                        "rating": fb.rating,
                        "comments": fb.comments
                    } for fb in feedbacks
                ]
            })
        return {"data": data}
    except Exception as e:
        print(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve database records")
    finally:
        db.close()

@app.get('/')
def home():
    return {
        "message": "The API is working"
    }

# Health check endpoint
@app.get('/health')
def health_check():
    return {
        "database": "connected and running" if engine else "not connected server has errors"
    }

if __name__ == "__main__":
    uvicorn.run("feedbacksytem:app", host="0.0.0.0", port=8000, log_level="info")