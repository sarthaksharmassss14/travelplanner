from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os
from utils import get_weather_info

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

prompt_template = PromptTemplate(
    input_variables=["destination", "days", "budget", "interests", "weather_info"],
    template="""
You are a travel assistant.
Create a detailed day-wise travel itinerary for {destination} lasting {days} days.
The total budget is {budget} INR.
Traveler is interested in: {interests}.
Current weather in {destination} is: {weather_info}.
Suggest local experiences, popular spots, and local foods.
Include estimated daily costs, travel tips, and safety notes.
Make it realistic and friendly.

Return itinerary in this format:
Day 1: ...
Day 2: ...
...
Total Estimate: ...

Start planning:
"""
)



def generate_itinerary(destination, days, budget, interests, travel_style="budget"):

    weather_info = get_weather_info(destination)
    
    # Get Gemini's dynamic estimate
    cost_estimates = get_cost_estimates(destination, days, travel_style)


    # Append cost breakdown to interests or inject it creatively into the prompt
    interests_with_costs = f"{interests}. Estimated costs: {cost_estimates}"
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)
    chain = LLMChain(llm=llm, prompt=prompt_template)
    result = chain.run({
        "destination": destination,
        "days": str(days),
        "budget": budget,
        "interests": interests_with_costs,
        "weather_info": weather_info
    })
    return cost_estimates, result




def get_cost_estimates(destination, days, travel_style):
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)

    cost_prompt = f"""
You are a travel expert. Estimate the following costs (in INR) for a {days}-day {travel_style.lower()} trip from India to {destination}.

Return your answer in this exact format:

| Category             | Cost (INR)      | Notes                            |
|----------------------|----------------|----------------------------------|
| Flight (round trip)  | INR XXXXX       | Budget airline from major city  |
| Accommodation        | INR XXXXX       | {travel_style} hotel/hostel     |
| Local Transport      | INR XXXXX       | Metro, buses, local transport   |
| Food & Dining        | INR XXXXX/day   | Local affordable meals          |
| Activities           | INR XXXXX/day   | Attractions, entry tickets      |
| Miscellaneous        | INR XXXXX       | Visa, insurance, etc.           |
| **Total Estimate**   | INR XXXXX       | For {days} days total           |
"""

    result = llm.invoke(cost_prompt)

    # Handle tuple or object
    if isinstance(result, tuple):
        return result[0]
    else:
        return getattr(result, 'content', str(result))
