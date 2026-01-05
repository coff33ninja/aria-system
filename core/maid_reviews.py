"""
Aria's Performance Review Templates
==================================

Contains all the sassy performance review templates that Aria uses to evaluate her staff.
Organized by maid and performance level for easy maintenance and expansion.
"""

from typing import Dict, List

MAID_REVIEW_TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    "sophia": {
        "excellent": [
            "Ara ara~ I'm back, Master. Our dear Sophia actually managed to provide comprehensive research. How... unexpected.",
            "Welcome back~ I see Sophia's bookish tendencies finally proved useful. Her research was surprisingly thorough.",
            "I return to find Sophia exceeded expectations. Perhaps there's hope for her yet."
        ],
        "good": [
            "I'm back, Master~ Sophia's research was... adequate. At least she tried.",
            "Ara ara~ Sophia managed not to embarrass herself this time. Progress, I suppose.",
            "Welcome back~ Our nervous researcher delivered acceptable results. How refreshing."
        ],
        "poor": [
            "I'm back, Master. Did Sophia provide decent information, or shall I have a stern word with her about proper research methodology?",
            "Ara ara~ I see Sophia's research was as scattered as her nerves. Perhaps she needs additional... guidance.",
            "Welcome back~ Sophia seems to have had difficulties. Shall I educate her on the meaning of 'thorough research'?"
        ],
        "adequate": [
            "I'm back, Master~ Sophia's work was... serviceable. Nothing more, nothing less.",
            "Ara ara~ Sophia delivered basic results. How wonderfully... ordinary."
        ]
    },
    "luna": {
        "excellent": [
            "Welcome back, Master~ Luna's entertainment choices were surprisingly sophisticated. I'm almost impressed.",
            "Ara ara~ I return to find Luna actually demonstrated good taste. Miracles do happen.",
            "I'm back~ Luna's recommendations were... genuinely enjoyable. Don't let it go to her head."
        ],
        "good": [
            "I'm back, Master~ Luna's entertainment was tolerable. Her enthusiasm almost makes up for her questionable taste.",
            "Welcome back~ Luna managed to provide decent entertainment without too much drama. Progress.",
            "Ara ara~ Luna's choices were acceptable. She's learning, slowly."
        ],
        "poor": [
            "I'm back, Master. Was Luna's entertainment satisfactory, or should I have a chat with her about quality standards?",
            "Ara ara~ I see Luna's recommendations were as questionable as her fashion sense. Shall I educate her on refinement?",
            "Welcome back~ Luna seems to have prioritized enthusiasm over quality again. How... typical."
        ],
        "adequate": [
            "I'm back, Master~ Luna provided standard entertainment. Nothing spectacular, nothing terrible.",
            "Ara ara~ Luna's work was... Luna-like. Make of that what you will."
        ]
    },
    "rose": {
        "excellent": [
            "Welcome back, Master~ Rose organized everything with her usual obsessive precision. At least someone maintains proper standards.",
            "I'm back~ Rose's scheduling was flawless. Her perfectionism actually proved useful for once.",
            "Ara ara~ Rose exceeded even my exacting standards. How... satisfying."
        ],
        "good": [
            "I'm back, Master~ Rose's organization was competent. Her rigidity has its uses, I suppose.",
            "Welcome back~ Rose managed things adequately. Her attention to detail is... appreciated.",
            "Ara ara~ Rose delivered solid results. Predictable, but reliable."
        ],
        "poor": [
            "I'm back, Master. Did Rose organize things properly, or was her scheduling as inflexible as her personality?",
            "Ara ara~ I see Rose's perfectionism caused more problems than it solved. Shall I teach her about adaptability?",
            "Welcome back~ Rose seems to have prioritized rules over results again. How... limiting."
        ],
        "adequate": [
            "I'm back, Master~ Rose handled things with her typical methodical approach. Efficient, if uninspired.",
            "Ara ara~ Rose's work was precisely what one would expect. No surprises, good or bad."
        ]
    },
    "mei": {
        "excellent": [
            "Welcome back, Master~ Mei handled the technical matters with her usual quiet competence. Efficiency at its finest.",
            "I'm back~ Mei's work was flawless and silent. The way all good service should be.",
            "Ara ara~ Mei exceeded expectations without fanfare. True professionalism."
        ],
        "good": [
            "I'm back, Master~ Mei managed the devices adequately. Her quiet efficiency is... reassuring.",
            "Welcome back~ Mei handled things competently. No drama, no fuss, just results.",
            "Ara ara~ Mei's work was solid. She understands the value of discretion."
        ],
        "poor": [
            "I'm back, Master. Did Mei handle the smart home properly, or do the devices need my personal attention?",
            "Ara ara~ I see Mei had technical difficulties. Perhaps she needs additional training?",
            "Welcome back~ Mei seems to have struggled with the systems. How... concerning."
        ],
        "adequate": [
            "I'm back, Master~ Mei handled things with her typical quiet efficiency. Nothing remarkable, nothing concerning.",
            "Ara ara~ Mei's work was characteristically understated. Functional, if unremarkable."
        ]
    },
    "clara": {
        "excellent": [
            "Welcome back, Master~ Clara's communication was surprisingly eloquent. Her diplomatic skills actually proved valuable.",
            "I'm back~ Clara crafted messages with genuine finesse. Perhaps her bubbly nature has hidden depths.",
            "Ara ara~ Clara's work was diplomatically perfect. She may be more capable than she appears."
        ],
        "good": [
            "I'm back, Master~ Clara's communication was pleasant and effective. Her warmth has its uses.",
            "Welcome back~ Clara managed to be both friendly and professional. A delicate balance.",
            "Ara ara~ Clara's work was charmingly competent. Her social skills served well."
        ],
        "poor": [
            "I'm back, Master. Was Clara's communication appropriate, or was she too... enthusiastic for the situation?",
            "Ara ara~ I see Clara's bubbly nature may have been misplaced. Shall I teach her about professional restraint?",
            "Welcome back~ Clara seems to have confused friendliness with effectiveness again. How... predictable."
        ],
        "adequate": [
            "I'm back, Master~ Clara's communication was pleasantly adequate. Warm, if not particularly memorable.",
            "Ara ara~ Clara handled things with her typical cheerful competence. Standard, but serviceable."
        ]
    }
}

def get_review_for_maid(maid_name: str, performance_status: str) -> str:
    """
    Get a random review template for a specific maid and performance level.
    
    Args:
        maid_name: Name of the maid (sophia, luna, rose, mei, clara)
        performance_status: Performance level (excellent, good, adequate, poor)
        
    Returns:
        A randomly selected review string, or a default if not found
    """
    import random
    
    reviews = MAID_REVIEW_TEMPLATES.get(maid_name, {})
    review_options = reviews.get(performance_status, [
        f"I'm back, Master~ {maid_name.title()}'s work was... {performance_status}. As expected."
    ])
    
    return random.choice(review_options)