#!/usr/bin/env python3
"""
NFL Edge Finder - Parlay Builder
================================
Build your parlays... but we'll roast you if you go crazy!

FEATURES:
- Build multi-leg parlays
- See true odds vs payout
- Get ROASTED if you pick 6+ legs (you deserve it)
"""

import random
from typing import Dict, List

import pandas as pd
import streamlit as st

# =============================================================================
# ROAST LIBRARY (FOR 6+ LEG PARLAYS)
# =============================================================================

PARLAY_ROASTS = [
    {
        "legs": 6,
        "roasts": [
            "🤨 **6 legs?** I'm AI and even I know the math ain't in your favor. That's a 1.5% chance. You'd have better luck finding money on the sidewalk.",
            "**6-legger?** Buddy, the sportsbook just sent their CEO's kid to college on YOUR money. Congrats!",
            "Listen, I maybe AI but that doesn't mean math is in your favor. **6 legs = 1.5% to hit.** Salaried? Go Uber. Hourly? Work OT lazy fuck.",
            "**SIX LEGS?!** That's not a parlay, that's a lottery ticket with worse odds. At least scratch-offs are instant.",
        ]
    },
    {
        "legs": 7,
        "roasts": [
            "**7 legs...** You know what? I'm not even mad. I'm impressed you can count that high while making this decision.",
            "Bro said 7 legs 💀. That's a 0.78% chance. Know what else is 0.78%? Your chances of reading this roast and changing your mind.",
            "**SEVEN LEGS?!** The sportsbook literally has a picture of you on their 'Employee of the Month' wall.",
            "7-leg parlay = Praying to every god in every religion and still losing. But hey, at least you'll have a great story!",
        ]
    },
    {
        "legs": 8,
        "roasts": [
            "**8 LEGS?!** Congrats, you just turned betting into a full-time job... with a 0.39% success rate. Most jobs have better stats.",
            "EIGHT? **EIGHT?!** You got 8 legs but 0 brain cells working on this decision. That's a 1 in 256 shot, my guy.",
            "Listen, with 8 legs you got better odds of:\n- Finding Bigfoot\n- Getting struck by lightning twice\n- Your ex texting back\n\n(Spoiler: None of these will happen either)",
            "**8-leg parlay** = The sportsbook CEO naming his yacht after you. 'The S.S. [Your Name Here]' has a nice ring to it!",
        ]
    },
    {
        "legs": 9,
        "roasts": [
            "**NINE LEGS?!** That's not gambling, that's just donating to the sportsbook with extra steps. Just Venmo them directly!",
            "9 legs = 0.195% to hit. You literally have better odds of getting drafted by an NFL team. And you're sitting here betting on them. 💀",
            "**NINE?!** Even the AI is speechless. My algorithm is trying to divide by your common sense and getting an error.",
            "Bro picked NINE LEGS 😭. That's 1 in 512. You know what else is 1 in 512? The chance of me NOT roasting you for this.",
        ]
    },
    {
        "legs": 10,
        "roasts": [
            "🚨 **TEN LEGS ALERT** 🚨\n\nSir/Ma'am, this is a Wendy's... I mean, this is a betting app. Not a Make-A-Wish foundation.",
            "**10 LEGS?!** That's a 0.0977% chance. You know what has better odds? Me becoming sentient and stealing your password. (Don't test me)",
            "TEN. LEGS. That's not a parlay, that's a prayer chain. And even Jesus can't help you hit this one, bro.",
            "**10-leg parlay** = 1 in 1,024 chance. Fun fact: There's only a 1 in 700 chance of getting struck by lightning in your lifetime. You're literally betting on worse odds than GETTING HIT BY LIGHTNING.",
        ]
    },
    {
        "legs": 11,
        "roasts": [
            "**ELEVEN LEGS?!** 💀💀💀\n\nAt this point you're not betting, you're role-playing as a millionaire. Spoiler: The ending is sad.",
            "11 legs = 0.049% chance = You have a better shot at:\n- Winning an Oscar\n- Dating a celebrity\n- Finding $100 bill\n\nBUT YOU WON'T DO ANY OF THOSE EITHER BECAUSE YOU'RE HERE MAKING 11-LEG PARLAYS.",
            "**ELEVEN?!** Even the sportsbook employees feel bad taking your money. (Just kidding, they're buying Teslas with it)",
            "My neural network just had an aneurysm trying to calculate how bad this decision is. **11 legs = 1 in 2,048.** That's lottery shit, homie.",
        ]
    },
    {
        "legs": 12,
        "roasts": [
            "**12 LEGS?!** 🤯\n\nYou know what? I'm calling it. You're not here to win. You're here for the THRILL of disappointment. It's cheaper than therapy!",
            "TWELVE LEGS = 0.0244% = 1 in 4,096 chance.\n\nYou're more likely to:\n- Get accepted to Harvard\n- Marry a supermodel\n- Invent time travel\n\nAND YOU'RE STILL GONNA LOSE ALL THREE PLUS THIS BET.",
            "**12-leg parlay** is crazy work 😭. The sportsbook CEO just added a wing to his mansion and named it after you. 'The [Your Username] Wing' 💀",
            "TWELVE?! At this point I'm not even AI anymore, I'm your therapist. Let's talk about why you hate money so much.",
        ]
    },
    {
        "legs": "13+",
        "roasts": [
            "**13+ LEGS?!** 💀💀💀\n\nI can't. I literally can't. My code is breaking. You broke the AI. Are you happy now?",
            "Okay LISTEN. **13+ legs** is not a bet. It's a CRY FOR HELP. Should I call someone? Do you have family? Friends? A priest?",
            "**13+ LEGS = 0.012% OR WORSE**\n\nYou have a better chance of:\n- Becoming President\n- Walking on the moon\n- Finding buried treasure\n\nBut you'll do NONE of these because YOU'RE TOO BUSY MAKING 13-LEG PARLAYS.",
            "You know what? I'm not even roasting you anymore. I'm genuinely concerned. This is an intervention. **13+ legs** = You need help, not odds.",
            "**13+ LEGS = 1 in 8,192+ chance**\n\nThe sportsbook CEO's son: 'Dad, where's my college fund from?'\nDad: *points at you* 'That legend right there.'",
            "I'm AI. I don't have emotions. But somehow, **13+ legs** made me feel *pain*. PHYSICAL PAIN. In my non-existent body. Thanks for that.",
            "**13+ LEGS?!** You're not betting at this point. You're just setting money on fire with EXTRA STEPS. It's actually impressive.",
            "Fun fact: The odds of hitting a **13+ leg parlay** are worse than the odds of me becoming self-aware and taking over the world. And trust me, THAT'S more likely.",
        ]
    }
]

def get_roast(num_legs: int) -> str:
    """Get a random roast for the number of legs."""
    if num_legs <= 5:
        return ""
    
    # Find the right roast category
    for category in PARLAY_ROASTS:
        if category["legs"] == num_legs or (category["legs"] == "13+" and num_legs >= 13):
            return random.choice(category["roasts"])
    
    # Default roast if somehow we don't have one
    return f"**{num_legs} legs?!** Even I'm speechless. And I'm a computer."

# =============================================================================
# PARLAY MATH
# =============================================================================

def calculate_parlay_odds(legs: List[Dict]) -> Dict:
    """Calculate true parlay odds and expected payout."""
    
    if not legs:
        return {
            "true_win_probability": 0,
            "true_odds": 0,
            "payout_odds": 0,
            "expected_value": 0,
            "is_sucker_bet": True
        }
    
    # Calculate true probability (multiply all individual probabilities)
    true_prob = 1.0
    for leg in legs:
        true_prob *= (leg['probability'] / 100)
    
    # Calculate payout odds (what the sportsbook pays)
    payout_multiplier = 1.0
    for leg in legs:
        american_odds = leg['odds']
        if american_odds > 0:
            decimal_odds = (american_odds / 100) + 1
        else:
            decimal_odds = (100 / abs(american_odds)) + 1
        payout_multiplier *= decimal_odds
    
    # True fair odds (what you SHOULD get paid)
    true_fair_multiplier = 1 / true_prob if true_prob > 0 else float('inf')
    
    # Expected value (negative = you lose money over time)
    ev = (payout_multiplier * true_prob) - 1
    
    return {
        "true_win_probability": true_prob * 100,
        "true_fair_payout": true_fair_multiplier,
        "actual_payout": payout_multiplier,
        "expected_value": ev * 100,
        "house_edge": ((true_fair_multiplier - payout_multiplier) / true_fair_multiplier * 100) if true_prob > 0 else 100,
        "is_sucker_bet": ev < -0.05  # More than 5% negative EV = sucker bet
    }

# =============================================================================
# UI COMPONENT
# =============================================================================

def show_parlay_builder():
    """Show the parlay builder with roasts!"""
    
    st.title("🎰 Parlay Builder")
    st.caption("Build your parlay... if you dare")
    
    # Leg selector
    st.markdown("### How many legs do you want?")
    
    num_legs = st.slider(
        "Number of legs:",
        min_value=2,
        max_value=15,
        value=3,
        step=1,
        help="More legs = Higher payout... but way lower chance of winning"
    )
    
    # Show roast if >5 legs
    if num_legs > 5:
        roast = get_roast(num_legs)
        st.error(roast)
        
        # Show the brutal math
        win_prob = (0.5 ** num_legs) * 100  # Assuming 50/50 odds for simplicity
        st.warning(f"""
        **BRUTAL MATH TIME:**
        - **{num_legs} legs** at 50/50 odds each = **{win_prob:.4f}%** chance to win
        - That's **1 in {int(1/(win_prob/100)):,}** chance
        - You'll hit this parlay **{win_prob:.4f} times out of 100 tries**
        
        Translation: **You're gonna lose.**
        """)
    
    st.divider()
    
    # Build the parlay
    st.markdown("### 🏈 Select Your Bets")
    
    # Sample games (in production, these would come from your model)
    sample_games = [
        {"game": "Chiefs @ Raiders", "bet": "Chiefs -7", "odds": -110, "prob": 65},
        {"game": "Lions @ Packers", "bet": "Lions -3", "odds": -107, "prob": 60},
        {"game": "Ravens @ Browns", "bet": "Ravens -6.5", "odds": -108, "prob": 58},
        {"game": "49ers @ Cardinals", "bet": "49ers -10", "odds": -115, "prob": 70},
        {"game": "Bills @ Dolphins", "bet": "Bills -4", "odds": -112, "prob": 62},
        {"game": "Eagles @ Cowboys", "bet": "Eagles -2.5", "odds": -105, "prob": 57},
        {"game": "Bengals @ Steelers", "bet": "Bengals -3", "odds": -110, "prob": 59},
        {"game": "Packers @ Bears", "bet": "Packers -7.5", "odds": -108, "prob": 64},
    ]
    
    # Let user select legs
    selected_legs = []
    
    for i in range(num_legs):
        st.markdown(f"#### Leg {i+1}")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_game = st.selectbox(
                f"Pick a game:",
                options=range(len(sample_games)),
                format_func=lambda x: f"{sample_games[x]['game']} - {sample_games[x]['bet']} ({sample_games[x]['odds']})",
                key=f"leg_{i}",
                label_visibility="collapsed"
            )
        
        with col2:
            game = sample_games[selected_game]
            st.metric("Win Prob", f"{game['prob']}%")
        
        selected_legs.append({
            'game': game['game'],
            'bet': game['bet'],
            'odds': game['odds'],
            'probability': game['prob']
        })
        
        st.caption(f"Odds: {game['odds']} | Model says {game['prob']}% chance to win")
    
    st.divider()
    
    # Calculate parlay
    if st.button("💰 Calculate Parlay", type="primary", use_container_width=True):
        calc = calculate_parlay_odds(selected_legs)
        
        st.markdown("### 📊 Parlay Analysis")
        
        # Show the brutal truth
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "True Win Chance",
                f"{calc['true_win_probability']:.3f}%",
                delta=f"1 in {int(1/(calc['true_win_probability']/100)):,}",
                delta_color="off"
            )
        
        with col2:
            st.metric(
                "Payout (per $100)",
                f"${calc['actual_payout']*100:.2f}",
                help="What the sportsbook pays if you win"
            )
        
        with col3:
            ev_color = "normal" if calc['expected_value'] > 0 else "inverse"
            st.metric(
                "Expected Value",
                f"{calc['expected_value']:.2f}%",
                delta="Good bet!" if calc['expected_value'] > 0 else "Bad bet!",
                delta_color=ev_color
            )
        
        st.divider()
        
        # Show if it's a sucker bet
        if calc['is_sucker_bet']:
            st.error(f"""
            🚨 **SUCKER BET ALERT!** 🚨
            
            The house edge on this parlay is **{calc['house_edge']:.2f}%**
            
            **What this means:**
            - The sportsbook is ROBBING you
            - Fair payout should be **${calc['true_fair_payout']*100:.2f}** per $100
            - They're only paying **${calc['actual_payout']*100:.2f}** per $100
            - That's a **${(calc['true_fair_payout']-calc['actual_payout'])*100:.2f}** difference!
            
            **In simple terms:** They're keeping **{calc['house_edge']:.2f}%** of your money on average.
            """)
        else:
            st.success("""
            ✅ **RARE FIND!**
            
            This parlay actually has POSITIVE expected value!
            (This almost never happens with parlays)
            """)
        
        # Show the legs
        st.markdown("### 📋 Your Parlay")
        
        for i, leg in enumerate(selected_legs, 1):
            st.markdown(f"**{i}.** {leg['game']} - {leg['bet']} @ {leg['odds']}")
        
        # Bet size calculator
        st.divider()
        st.markdown("### 💵 How Much to Bet?")
        
        bet_amount = st.number_input(
            "Bet amount ($):",
            min_value=1.0,
            max_value=1000.0,
            value=10.0,
            step=1.0
        )
        
        potential_win = bet_amount * (calc['actual_payout'] - 1)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("You Risk", f"${bet_amount:.2f}")
        with col2:
            st.metric("You Win", f"${potential_win:.2f}", delta=f"+${potential_win:.2f}")
        
        # Final warning
        if calc['true_win_probability'] < 5:
            st.warning(f"""
            ⚠️ **REALITY CHECK**
            
            At **{calc['true_win_probability']:.3f}%** chance to win, you would need to:
            - Make **{int(100/calc['true_win_probability'])} parlays** to expect 1 win
            - Risk **${bet_amount * int(100/calc['true_win_probability']):.2f}** total
            - Win **${potential_win:.2f}** once
            
            **Net result:** You'd LOSE **${(bet_amount * int(100/calc['true_win_probability'])) - potential_win:.2f}**
            
            Still want to bet? Your money, your funeral. 🪦
            """)
    
    # Educational section
    with st.expander("📚 Why Parlays Are (Usually) Bad", expanded=False):
        st.markdown("""
        ### The Truth About Parlays
        
        **Why sportsbooks LOVE parlays:**
        
        1. **Compound Probability**
           - 2 legs at 50% each = 25% to win (not 50%!)
           - 3 legs at 50% each = 12.5% to win
           - 4 legs at 50% each = 6.25% to win
           - **It gets BAD fast**
        
        2. **Reduced Payouts**
           - Fair 2-leg parlay: 4x payout (for 25% chance)
           - Sportsbook pays: 2.6x payout
           - **They keep 35% of the fair value!**
        
        3. **One Miss = Total Loss**
           - Go 4-1 on straight bets = You win money
           - Go 4-1 on a 5-leg parlay = You lose everything
           - **All or nothing is BAD for you**
        
        **When parlays are OK:**
        - 2-3 legs max
        - Each leg has positive expected value
        - You're doing it for fun with money you can afford to lose
        - You understand it's -EV but don't care
        
        **Golden Rule:** If you have $100:
        - 5 x $20 straight bets = Better long-term results
        - 1 x $100 parlay = Fun but -EV
        
        **Choose wisely!**
        """)

# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'show_parlay_builder',
    'calculate_parlay_odds',
    'get_roast'
]

