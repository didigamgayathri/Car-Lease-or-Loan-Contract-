"""
FastAPI Backend for Car Contract AI
Provides endpoints for contract analysis and chatbot negotiation advice.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import pdfplumber
import io

from analyzer import analyze_contract

app = FastAPI(title="Car Contract AI API", version="1.0.0")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    message: str
    contract_info: Optional[dict] = None


class ChatResponse(BaseModel):
    response: str


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Car Contract AI API is running"}


@app.post("/analyze")
async def analyze_contract_endpoint(file: UploadFile = File(...)):
    """
    Analyze a PDF contract file.
    Extracts text from PDF and performs AI analysis.
    """
    try:
        # Check if file is PDF
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are accepted")
        
        # Read the file content
        file_content = await file.read()
        
        # Extract text from PDF
        text = extract_text_from_pdf(file_content)
        
        if not text or len(text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Could not extract sufficient text from PDF")
        
        # Analyze the contract
        result = analyze_contract(text)
        
        # Add filename to result
        result["filename"] = file.filename
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing contract: {str(e)}")


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        # If pdfplumber fails, try to return a sample analysis
        # This allows testing without valid PDF
        print(f"PDF extraction error: {e}")
        raise
    
    return text


@app.post("/chatbot")
async def chatbot_endpoint(chat_message: ChatMessage):
    """
    Chatbot endpoint for negotiation advice.
    Provides responses based on contract info and user questions.
    """
    message = chat_message.message.lower()
    contract_info = chat_message.contract_info or {}
    
    response = generate_chatbot_response(message, contract_info)
    
    return {"response": response}


def generate_chatbot_response(message: str, contract_info: dict) -> str:
    """Generate chatbot response based on user message and contract info."""
    
    # Get key contract details
    apr = contract_info.get("apr", "unknown")
    monthly_payment = contract_info.get("monthly_payment", "unknown")
    mileage_limit = contract_info.get("mileage_limit", "unknown")
    fairness_score = contract_info.get("fairness_score", 0)
    risk_rating = contract_info.get("risk_rating", "unknown")
    risks = contract_info.get("risks", [])
    
    # Question: Is this lease fair?
    if "fair" in message or "good" in message or "worth" in message:
        if fairness_score >= 70:
            return f"Based on the analysis, this appears to be a {fairness_score}% fair lease. The terms are generally reasonable, but there's always room for negotiation. Would you like specific tips?"
        elif fairness_score >= 40:
            return f"This lease has a {fairness_score}% fairness score, which is moderate. There are some areas that could be improved. The main concerns are: {', '.join(risks[:2]) if risks else 'standard terms'}. Would you like negotiation advice?"
        else:
            return f"This lease has a low fairness score ({fairness_score}%). The terms seem unfavorable. Key issues include: {', '.join(risks[:3]) if risks else 'various concerns'}. I strongly recommend negotiating harder or considering alternatives."
    
    # Question: Can I negotiate APR?
    elif "apr" in message or "interest" in message or "rate" in message:
        try:
            apr_val = float(apr.replace("%", ""))
            if apr_val > 7:
                return f"Absolutely! The current APR of {apr} is above market average (5-7%). You should definitely negotiate for a lower rate. Start by saying you're comparing offers from multiple lenders and ask if they can match a lower rate."
            elif apr_val > 5:
                return f"The APR of {apr} is slightly above average. You can try negotiating, but the room for improvement may be limited. Mention that you have good credit and ask for a better rate."
            else:
                return f"The APR of {apr} is at or below market average. While you can always try to negotiate, focus your efforts on other areas like waived fees or mileage limits instead."
        except:
            return "I couldn't detect the APR from the contract. Could you check the contract for the APR percentage? This is one of the most important numbers to negotiate."
    
    # Question: What should I ask the dealer?
    elif "ask" in message or "dealer" in message or "negotiat" in message:
        tips = []
        if contract_info.get("negotiation_tips"):
            tips = contract_info.get("negotiation_tips", [])[:3]
            return f"Here are the top things you should ask the dealer:\n\n" + "\n".join([f"• {tip}" for tip in tips])
        else:
            return "I recommend asking the dealer to:\n\n• Waive the acquisition and documentation fees\n• Reduce the APR\n• Increase the mileage limit\n• Remove the early termination penalty\n• Lower the capitalized cost of the vehicle"
    
    # Question: Monthly payment concerns
    elif "monthly" in message or "payment" in message:
        return f"The monthly payment is {monthly_payment}. While this is important, focus on the total cost of the lease including all fees. The best negotiation tactic is to negotiate the capitalized cost (vehicle price) first, then discuss monthly payments."
    
    # Question: Mileage concerns
    elif "mileage" in message or "mile" in message:
        return f"The mileage limit is {mileage_limit} per year. If you drive more than this, you'll be charged excess mileage fees (typically 15-25 cents per mile). Negotiate for at least 15,000 miles/year, or consider a shorter lease if your driving needs vary."
    
    # Question: Early termination
    elif "terminate" in message or "end" in message or "cancel" in message:
        if contract_info.get("early_termination"):
            return "The contract has an early termination clause. Ask the dealer to remove or reduce this penalty. You never know when your circumstances might change, and this protection is valuable."
        else:
            return "Good news - I didn't detect an early termination fee in the contract. This gives you more flexibility if you need to end the lease early."
    
    # Question: Hidden fees
    elif "fee" in message or "hidden" in message or "extra" in message:
        if risks:
            fee_related = [r for r in risks if "fee" in r.lower()]
            if fee_related:
                return f"I detected these potential fee-related issues:\n\n" + "\n".join([f"• {r}" for r in fee_related]) + "\n\nAlways ask the dealer to explain every fee in detail and request waivers for unnecessary charges."
        return "Always ask for a complete breakdown of all fees. Common negotiable fees include: acquisition fee, documentation fee, disposition fee, and registration fees. Request that these be waived or reduced."
    
    # Question: Risk assessment
    elif "risk" in message or "danger" in message or "concern" in message:
        return f"Based on the analysis, the risk rating is: {risk_rating}.\n\n" + ("The main risks are:\n\n" + "\n".join([f"• {r}" for r in risks[:4]]) if risks else "No major risks detected.")
    
    # Question: Hello/Hi
    elif "hello" in message or "hi" in message or "hey" in message:
        return "Hello! I'm your car contract negotiation assistant. I can help you understand if a lease is fair, what to negotiate, and how to get the best deal. What would you like to know?"
    
    # Question: Help
    elif "help" in message or "what can you" in message:
        return "I can help you with:\n\n• Is this lease fair?\n• Can I negotiate the APR?\n• What should I ask the dealer?\n• Are there hidden fees?\n• What's the risk level?\n• And more!\n\nJust ask me a question about your contract."
    
    # Default response
    else:
        return "I'm here to help you negotiate the best car lease deal. Ask me questions like:\n\n• Is this lease fair?\n• Can I negotiate the APR?\n• What should I ask the dealer?\n\nI'll provide personalized advice based on your contract analysis!"


# Mock data storage for recent analyses (in-memory)
recent_analyses = []


@app.get("/recent")
async def get_recent_analyses():
    """Get recent contract analyses."""
    return recent_analyses[-10:]  # Return last 10 analyses


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
