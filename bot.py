# Arbitrage Betting Bot with OddsAPI, Alerts, and Dashboard

import requests
import time
import math
import streamlit as st
import smtplib
from email.message import EmailMessage
import os

# === Configuration ===
API_KEY = os.getenv('ODDS_API_KEY')
SPORT = 'soccer_epl'
EMAIL_ALERTS = True
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# === Functions ===
def fetch_odds(api_key, sport=SPORT):
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
    params = {
        'apiKey': api_key,
        'regions': 'uk,us',
        'markets': 'h2h',
        'oddsFormat': 'decimal'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching odds: {e}")
        return []

def find_arbitrage(odds_data):
    opportunities = []
    for match in odds_data:
        try:
            teams = match['teams']
            bookmakers = match['bookmakers']
            for i in range(len(bookmakers)):
                for j in range(i + 1, len(bookmakers)):
                    market1 = bookmakers[i]['markets'][0]['outcomes']
                    market2 = bookmakers[j]['markets'][0]['outcomes']
                    odds1 = market1[0]['price']
                    odds2 = market2[1]['price']
                    arb_value = (1 / odds1) + (1 / odds2)
                    if arb_value < 1:
                        profit_margin = round((1 - arb_value) * 100, 2)
                        opportunities.append({
                            'teams': teams,
                            'bookmaker1': bookmakers[i]['title'],
                            'bookmaker2': bookmakers[j]['title'],
                            'odds1': odds1,
                            'odds2': odds2,
                            'profit_margin': profit_margin
                        })
        except:
            continue
    return opportunities

def send_email_alert(opp):
    try:
        msg = EmailMessage()
        msg['Subject'] = f"Arbitrage Alert: {opp['teams']}"
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_ADDRESS
        body = f"Match: {opp['teams']}\nProfit: {opp['profit_margin']}%\n{opp['bookmaker1']} odds: {opp['odds1']}\n{opp['bookmaker2']} odds: {opp['odds2']}"
        msg.set_content(body)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("Email sent.")
    except Exception as e:
        print(f"Email alert failed: {e}")

# === Streamlit Dashboard ===
def run_dashboard():
    st.title("📈 Arbitrage Sports Betting Bot")
    odds_data = fetch_odds(API_KEY)
    opps = find_arbitrage(odds_data)

    if opps:
        st.success(f"{len(opps)} arbitrage opportunities found!")
        for opp in opps:
            st.write(f"### {opp['teams']}")
            st.write(f"- Bookmakers: {opp['bookmaker1']} & {opp['bookmaker2']}")
            st.write(f"- Odds: {opp['odds1']} / {opp['odds2']}")
            st.write(f"- Profit Margin: {opp['profit_margin']}% ✅")
            st.markdown("---")
            if EMAIL_ALERTS:
                send_email_alert(opp)
    else:
        st.warning("No arbitrage opportunities at the moment. Try again later.")

if __name__ == "__main__":
    run_dashboard()
