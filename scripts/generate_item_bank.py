"""Generate the english_test_items_v1.json dataset."""
from __future__ import annotations

import json
from pathlib import Path

level_data = {
    "A1": {
        "grammar": [
            {"prompt": "I ___ breakfast at 7 o'clock every day.", "options": ["eat", "eats", "eating", "ate"], "answer": "eat"},
            {"prompt": "They ___ in a small town.", "options": ["live", "lives", "living", "lived"], "answer": "live"},
            {"prompt": "She ___ English on Mondays.", "options": ["study", "studies", "studying", "studied"], "answer": "studies"},
            {"prompt": "We ___ happy to see you.", "options": ["are", "am", "is", "be"], "answer": "are"},
            {"prompt": "My brother ___ tall.", "options": ["is", "are", "be", "being"], "answer": "is"},
            {"prompt": "___ you like coffee?", "options": ["Do", "Does", "Is", "Are"], "answer": "Do"},
            {"prompt": "There ___ a cat on the sofa.", "options": ["is", "are", "be", "been"], "answer": "is"},
            {"prompt": "He ___ his bike to school.", "options": ["rides", "ride", "riding", "rode"], "answer": "rides"},
        ],
        "vocab": [
            {"prompt": "Choose the word that means the opposite of 'hot'.", "options": ["cold", "warm", "boiling", "spicy"], "answer": "cold"},
            {"prompt": "Select the word that names a piece of furniture.", "options": ["table", "apple", "shoe", "glass"], "answer": "table"},
            {"prompt": "Which word is a color?", "options": ["blue", "bread", "chair", "clock"], "answer": "blue"},
            {"prompt": "Choose the word that best completes the sentence: I have a ___ friend.", "options": ["good", "fast", "slow", "late"], "answer": "good"},
            {"prompt": "Pick the correct word for this definition: a place where you buy medicine.", "options": ["pharmacy", "library", "kitchen", "garage"], "answer": "pharmacy"},
            {"prompt": "Find the word that names an animal.", "options": ["dog", "desk", "door", "dish"], "answer": "dog"},
            {"prompt": "Choose the word that means 'fast'.", "options": ["quick", "quiet", "question", "queue"], "answer": "quick"},
            {"prompt": "Select the word that completes the sentence: It's a sunny ___.", "options": ["day", "book", "shoe", "plate"], "answer": "day"},
        ],
        "reading": [
            {"prompt": "Read: 'Maria likes apples and bananas.' What does Maria like?", "options": ["Apples and bananas", "Oranges", "Grapes", "Peaches"], "answer": "Apples and bananas"},
            {"prompt": "Read: 'The bus arrives at nine o'clock.' When does the bus arrive?", "options": ["At nine o'clock", "At ten", "At eight", "At noon"], "answer": "At nine o'clock"},
            {"prompt": "Read: 'Tom has two sisters and one brother.' How many sisters does Tom have?", "options": ["Two", "Three", "One", "Four"], "answer": "Two"},
            {"prompt": "Read: 'The store is closed on Sunday.' Which day is the store closed?", "options": ["Sunday", "Monday", "Friday", "Saturday"], "answer": "Sunday"},
            {"prompt": "Read: 'Anna drinks water every morning.' What does Anna drink?", "options": ["Water", "Coffee", "Tea", "Juice"], "answer": "Water"},
            {"prompt": "Read: 'The teacher writes on the board.' Where does the teacher write?", "options": ["On the board", "On the floor", "On the door", "On the book"], "answer": "On the board"},
            {"prompt": "Read: 'Peter walks to work because it is close.' Why does Peter walk to work?", "options": ["Because it is close", "Because it rains", "Because he likes cars", "Because he is late"], "answer": "Because it is close"},
            {"prompt": "Read: 'Sara has a new blue jacket.' What color is Sara's jacket?", "options": ["Blue", "Red", "Green", "Yellow"], "answer": "Blue"},
        ],
        "use_of_english": [
            {"prompt": "Choose the correct word: I usually go to work ___ bus.", "options": ["by", "in", "at", "on"], "answer": "by"},
            {"prompt": "Select the correct phrase: Could you ___ me, please?", "options": ["help", "helps", "helping", "helped"], "answer": "help"},
            {"prompt": "Pick the right option: We are going ___ the park this afternoon.", "options": ["to", "at", "in", "on"], "answer": "to"},
            {"prompt": "Choose the correct sentence order: always / I / breakfast / have / at / home.", "options": ["I always have breakfast at home.", "Always I have breakfast home at.", "I have always breakfast at home.", "I have breakfast always at home."], "answer": "I always have breakfast at home."},
            {"prompt": "Select the correct completion: He is ___ than his brother.", "options": ["taller", "tall", "more tall", "the tallest"], "answer": "taller"},
            {"prompt": "Pick the word that completes the sentence: There aren't ___ apples left.", "options": ["any", "some", "much", "many"], "answer": "any"},
            {"prompt": "Choose the correct option: I'm looking forward ___ you soon.", "options": ["to seeing", "seeing", "to see", "see"], "answer": "to seeing"},
            {"prompt": "Select the correct word: We went to the cinema ___ Friday.", "options": ["on", "in", "at", "to"], "answer": "on"},
        ],
    },
    "A2": {
        "grammar": [
            {"prompt": "She is ___ dinner right now.", "options": ["cooking", "cook", "cooks", "cooked"], "answer": "cooking"},
            {"prompt": "We have ___ the museum twice this month.", "options": ["visited", "visiting", "visit", "visits"], "answer": "visited"},
            {"prompt": "If it ___ tomorrow, we'll stay at home.", "options": ["rains", "rain", "rained", "is raining"], "answer": "rains"},
            {"prompt": "They ___ to move to Canada next year.", "options": ["plan", "plans", "planned", "are plan"], "answer": "plan"},
            {"prompt": "I ___ my homework before dinner yesterday.", "options": ["finished", "finish", "finishes", "finishing"], "answer": "finished"},
            {"prompt": "Have you ever ___ a kangaroo?", "options": ["seen", "saw", "see", "seeing"], "answer": "seen"},
            {"prompt": "By the time we arrived, the film ___ already started.", "options": ["had", "has", "have", "having"], "answer": "had"},
            {"prompt": "The book was ___ by a famous journalist.", "options": ["written", "write", "writing", "writes"], "answer": "written"},
        ],
        "vocab": [
            {"prompt": "Choose the best synonym for 'purchase'.", "options": ["buy", "sell", "borrow", "lend"], "answer": "buy"},
            {"prompt": "Select the correct word to complete the sentence: I need to ___ a decision soon.", "options": ["make", "do", "build", "take"], "answer": "make"},
            {"prompt": "Which word describes someone who likes meeting new people?", "options": ["friendly", "lonely", "lazy", "quiet"], "answer": "friendly"},
            {"prompt": "Choose the word that means 'journey'.", "options": ["trip", "meal", "dream", "gift"], "answer": "trip"},
            {"prompt": "Pick the correct word: The opposite of 'noisy' is ___.", "options": ["quiet", "loud", "busy", "open"], "answer": "quiet"},
            {"prompt": "Find the word that means 'to postpone'.", "options": ["delay", "decide", "deliver", "decorate"], "answer": "delay"},
            {"prompt": "Choose the best option for 'a person who designs buildings'.", "options": ["architect", "author", "pilot", "chef"], "answer": "architect"},
            {"prompt": "Select the word that completes the sentence: She felt ___ after running the race.", "options": ["exhausted", "exciting", "excitement", "exhaust"], "answer": "exhausted"},
        ],
        "reading": [
            {"prompt": "Read: 'Lucas enjoys hiking on the weekends because it helps him relax.' Why does Lucas like hiking?", "options": ["It helps him relax", "It is close to his home", "He can compete", "He earns money"], "answer": "It helps him relax"},
            {"prompt": "Read: 'The cafe closes earlier during winter due to the cold weather.' When does the cafe close earlier?", "options": ["During winter", "During summer", "On holidays", "On Mondays"], "answer": "During winter"},
            {"prompt": "Read: 'Emma moved to Berlin to study design at a university.' Why did Emma move to Berlin?", "options": ["To study design", "To visit friends", "To find work", "To learn German"], "answer": "To study design"},
            {"prompt": "Read: 'The local market sells fresh vegetables every Saturday morning.' What does the market sell?", "options": ["Fresh vegetables", "Books", "Furniture", "Clothes"], "answer": "Fresh vegetables"},
            {"prompt": "Read: 'Because the train was delayed, the passengers received free snacks.' What did passengers receive?", "options": ["Free snacks", "New tickets", "Hotel rooms", "Taxi rides"], "answer": "Free snacks"},
            {"prompt": "Read: 'The museum offers guided tours in English and French.' Which languages are the tours in?", "options": ["English and French", "Spanish and Italian", "German only", "English only"], "answer": "English and French"},
            {"prompt": "Read: 'Sara downloaded a language app to practice her Spanish vocabulary.' Why did Sara download the app?", "options": ["To practice Spanish vocabulary", "To watch movies", "To learn to code", "To track her fitness"], "answer": "To practice Spanish vocabulary"},
            {"prompt": "Read: 'The sports center closes at 8 p.m., so members must leave before then.' What time must members leave?", "options": ["Before 8 p.m.", "After 9 p.m.", "At midnight", "At 10 a.m."], "answer": "Before 8 p.m."},
        ],
        "use_of_english": [
            {"prompt": "Choose the correct phrase: We look forward ___ from you soon.", "options": ["to hearing", "hearing", "to hear", "hear"], "answer": "to hearing"},
            {"prompt": "Select the correct word: He has lived here ___ five years.", "options": ["for", "since", "during", "by"], "answer": "for"},
            {"prompt": "Pick the best option: If I were you, I ___ speak to the manager.", "options": ["would", "will", "can", "am"], "answer": "would"},
            {"prompt": "Choose the correct completion: She hasn't finished the report ___.", "options": ["yet", "still", "already", "just"], "answer": "yet"},
            {"prompt": "Select the correct collocation: My brother is afraid ___ flying.", "options": ["of", "from", "at", "with"], "answer": "of"},
            {"prompt": "Pick the right option: We need to pick ___ the keys before leaving.", "options": ["up", "on", "in", "out"], "answer": "up"},
            {"prompt": "Choose the correct sentence: ___ you ever tried Thai food?", "options": ["Have", "Do", "Did", "Are"], "answer": "Have"},
            {"prompt": "Select the best phrase: This is the person ___ car was stolen.", "options": ["whose", "who", "which", "whom"], "answer": "whose"},
        ],
    },
    "B1": {
        "grammar": [
            {"prompt": "If I ___ more time, I would take another class.", "options": ["had", "have", "has", "having"], "answer": "had"},
            {"prompt": "She said she ___ the documents before the meeting.", "options": ["had checked", "checked", "has checked", "was checking"], "answer": "had checked"},
            {"prompt": "When the phone rang, we ___ dinner.", "options": ["were eating", "ate", "had eaten", "eat"], "answer": "were eating"},
            {"prompt": "The project ___ by a multinational company last year.", "options": ["was acquired", "acquired", "is acquiring", "has acquiring"], "answer": "was acquired"},
            {"prompt": "He ___ to the doctor if the pain continues.", "options": ["will go", "goes", "went", "has gone"], "answer": "will go"},
            {"prompt": "By next Friday, we ___ the report.", "options": ["will have finished", "finish", "have finished", "finished"], "answer": "will have finished"},
            {"prompt": "I regret ___ him the news so late.", "options": ["telling", "to tell", "tell", "told"], "answer": "telling"},
            {"prompt": "Not only ___ the presentation, but she also negotiated the contract.", "options": ["did she lead", "she led", "led she", "does she lead"], "answer": "did she lead"},
        ],
        "vocab": [
            {"prompt": "Choose the best synonym for 'reliable'.", "options": ["dependable", "unpredictable", "temporary", "fragile"], "answer": "dependable"},
            {"prompt": "Select the word that means 'a strong desire to succeed'.", "options": ["ambition", "habit", "doubt", "routine"], "answer": "ambition"},
            {"prompt": "Which word refers to 'money paid for work'?", "options": ["salary", "expense", "budget", "donation"], "answer": "salary"},
            {"prompt": "Choose the option that best completes the sentence: The article provides a ___ overview of the topic.", "options": ["comprehensive", "complicated", "convenient", "careless"], "answer": "comprehensive"},
            {"prompt": "Pick the correct word: She has a very ___ attitude toward change.", "options": ["positive", "passive", "poisonous", "peculiar"], "answer": "positive"},
            {"prompt": "Find the word that means 'to persuade someone to do something'.", "options": ["convince", "contain", "convert", "conclude"], "answer": "convince"},
            {"prompt": "Choose the correct word for 'something that prevents progress'.", "options": ["obstacle", "opinion", "option", "orbit"], "answer": "obstacle"},
            {"prompt": "Select the best synonym for 'increase'.", "options": ["boost", "break", "borrow", "bounce"], "answer": "boost"},
        ],
        "reading": [
            {"prompt": "Read: 'The company introduced remote work policies to attract international talent.' Why did the company change its policies?", "options": ["To attract international talent", "To reduce office rent", "To test new software", "To open a new branch"], "answer": "To attract international talent"},
            {"prompt": "Read: 'After comparing several smartphones, Lina chose the one with the best camera.' What was important to Lina?", "options": ["Having the best camera", "Finding the cheapest phone", "Choosing the largest screen", "Buying a limited edition"], "answer": "Having the best camera"},
            {"prompt": "Read: 'During the workshop, participants practiced negotiation through role-playing exercises.' How did participants practice negotiation?", "options": ["Through role-playing", "By reading articles", "By watching videos", "Through written exams"], "answer": "Through role-playing"},
            {"prompt": "Read: 'The travel blog features stories from professionals who work while exploring new countries.' Who writes the stories?", "options": ["Professionals who travel", "Retired teachers", "Students on exchange", "Local journalists"], "answer": "Professionals who travel"},
            {"prompt": "Read: 'Because the conference was postponed, attendees rescheduled their flights for October.' What did attendees do after the conference was postponed?", "options": ["Rescheduled their flights", "Cancelled their hotels", "Changed the venue", "Requested refunds"], "answer": "Rescheduled their flights"},
            {"prompt": "Read: 'The city's recycling program expanded to include electronic devices such as tablets and laptops.' What items were added to the program?", "options": ["Electronic devices", "Furniture", "Plastic bottles", "Clothing"], "answer": "Electronic devices"},
            {"prompt": "Read: 'The research concluded that regular breaks improve concentration during long study sessions.' What improves concentration?", "options": ["Regular breaks", "Loud music", "Late-night studying", "Energy drinks"], "answer": "Regular breaks"},
            {"prompt": "Read: 'Eva joined a mentoring network to get feedback on her startup ideas.' Why did Eva join the network?", "options": ["To get feedback on her startup ideas", "To find a co-founder", "To promote a product", "To learn a new language"], "answer": "To get feedback on her startup ideas"},
        ],
        "use_of_english": [
            {"prompt": "Choose the correct phrase: The report must be handed in ___ Friday at noon.", "options": ["by", "until", "during", "since"], "answer": "by"},
            {"prompt": "Select the correct word: We couldn't attend the meeting because we ___ informed in time.", "options": ["weren't", "haven't", "didn't", "don't"], "answer": "weren't"},
            {"prompt": "Pick the best option: Hardly had we started the trip ___ it began to rain.", "options": ["when", "than", "because", "so"], "answer": "when"},
            {"prompt": "Choose the correct completion: She asked me ___ I had completed the assignment.", "options": ["whether", "because", "despite", "unless"], "answer": "whether"},
            {"prompt": "Select the correct collocation: They took advantage ___ the early-bird discount.", "options": ["of", "for", "at", "to"], "answer": "of"},
            {"prompt": "Pick the right option: The sooner you call, the ___ appointment you will get.", "options": ["better", "best", "more good", "most good"], "answer": "better"},
            {"prompt": "Choose the correct sentence: No sooner ___ the train left than it started snowing.", "options": ["had", "has", "have", "having"], "answer": "had"},
            {"prompt": "Select the best phrase: We should have the results ready by the time they ___.", "options": ["arrive", "arrived", "arrives", "are arriving"], "answer": "arrive"},
        ],
    },
    "B2": {
        "grammar": [
            {"prompt": "Had he ___ the warning signs, he might have avoided the mistake.", "options": ["noticed", "notice", "noticing", "notices"], "answer": "noticed"},
            {"prompt": "No sooner ___ the proposal presented than questions arose.", "options": ["was", "is", "has", "had"], "answer": "was"},
            {"prompt": "The committee insisted that the report ___ rewritten in plain language.", "options": ["be", "is", "was", "being"], "answer": "be"},
            {"prompt": "If she ___ the offer earlier, she would be working with us now.", "options": ["had accepted", "accepted", "accepts", "has accepted"], "answer": "had accepted"},
            {"prompt": "The new guidelines require employees ___ training every six months.", "options": ["to undergo", "undergo", "undergoing", "to be undergone"], "answer": "to undergo"},
            {"prompt": "Hardly ___ into the interview when the fire alarm sounded.", "options": ["had she settled", "she had settled", "she settled", "has she settled"], "answer": "had she settled"},
            {"prompt": "The data, together with the supporting documents, ___ available online.", "options": ["is", "are", "was", "has"], "answer": "are"},
            {"prompt": "Despite ___ a tight deadline, the team delivered exceptional work.", "options": ["facing", "face", "faced", "to face"], "answer": "facing"},
        ],
        "vocab": [
            {"prompt": "Choose the word that best completes the sentence: The scientist's theory was widely ___ by the community.", "options": ["endorsed", "ignored", "distracted", "disturbed"], "answer": "endorsed"},
            {"prompt": "Select the option closest in meaning to 'meticulous'.", "options": ["thorough", "reckless", "hasty", "casual"], "answer": "thorough"},
            {"prompt": "Which word describes a 'temporary halt in activity'?", "options": ["hiatus", "harmony", "harvest", "heritage"], "answer": "hiatus"},
            {"prompt": "Choose the best replacement for 'compelling' in the sentence 'She gave a compelling presentation'.", "options": ["persuasive", "convenient", "passive", "provincial"], "answer": "persuasive"},
            {"prompt": "Pick the word that means 'to make something less severe'.", "options": ["alleviate", "allocate", "allude", "alter"], "answer": "alleviate"},
            {"prompt": "Find the option that means 'capable of being believed'.", "options": ["plausible", "pliable", "palpable", "portable"], "answer": "plausible"},
            {"prompt": "Choose the best synonym for 'diligent'.", "options": ["hardworking", "indifferent", "lenient", "reserved"], "answer": "hardworking"},
            {"prompt": "Select the word meaning 'to strongly criticize publicly'.", "options": ["condemn", "conserve", "confer", "condense"], "answer": "condemn"},
        ],
        "reading": [
            {"prompt": "Read: 'The documentary highlights communities that adapted innovative farming techniques to combat drought.' What does the documentary highlight?", "options": ["Communities using innovative farming techniques", "Cities investing in highways", "Scientists debating climate data", "Artists discussing sustainable design"], "answer": "Communities using innovative farming techniques"},
            {"prompt": "Read: 'After extensive trials, the startup launched a platform that automates ethical supply-chain audits.' What did the startup release?", "options": ["A platform for ethical supply-chain audits", "A new marketing campaign", "An employee wellness program", "An electric delivery van"], "answer": "A platform for ethical supply-chain audits"},
            {"prompt": "Read: 'The journalist juxtaposed personal stories with statistics to emphasize the report's urgency.' How did the journalist emphasize urgency?", "options": ["By combining stories with statistics", "By using only numbers", "By ignoring interviews", "By shortening the report"], "answer": "By combining stories with statistics"},
            {"prompt": "Read: 'Because the policy lacked transparency, stakeholders demanded a revised framework.' Why did stakeholders demand a revision?", "options": ["The policy lacked transparency", "It cost too much", "It was too short", "It included interviews"], "answer": "The policy lacked transparency"},
            {"prompt": "Read: 'The engineer credited her success to mentors who challenged her assumptions.' What did mentors do?", "options": ["Challenged her assumptions", "Funded her company", "Hired her team", "Reduced her workload"], "answer": "Challenged her assumptions"},
            {"prompt": "Read: 'Participants concluded that collaborative leadership fosters more resilient teams.' What conclusion did participants reach?", "options": ["Collaborative leadership builds resilient teams", "Individual decisions are fastest", "Remote work hinders innovation", "Budgets should be reduced"], "answer": "Collaborative leadership builds resilient teams"},
            {"prompt": "Read: 'The research lab secured grants by demonstrating measurable environmental impact.' How did the lab secure grants?", "options": ["By demonstrating measurable environmental impact", "By hiring new marketers", "By cutting salaries", "By outsourcing production"], "answer": "By demonstrating measurable environmental impact"},
            {"prompt": "Read: 'Because the city prioritized public transport, commute times dropped significantly.' What happened to commute times?", "options": ["They dropped significantly", "They became unpredictable", "They increased slightly", "They remained unchanged"], "answer": "They dropped significantly"},
        ],
        "use_of_english": [
            {"prompt": "Choose the correct phrase: The initiative aims ___ reducing waste across the organization.", "options": ["at", "for", "to", "into"], "answer": "at"},
            {"prompt": "Select the correct word: Had it not been for her guidance, we ___ lost the client.", "options": ["would have", "will have", "would", "had"], "answer": "would have"},
            {"prompt": "Pick the best option: The CEO demanded that the report ___ submitted by Monday.", "options": ["be", "is", "was", "being"], "answer": "be"},
            {"prompt": "Choose the correct completion: Scarcely had the meeting started ___ the fire drill began.", "options": ["when", "than", "before", "after"], "answer": "when"},
            {"prompt": "Select the correct collocation: They attributed the breakthrough ___ years of experimentation.", "options": ["to", "for", "by", "from"], "answer": "to"},
            {"prompt": "Pick the right option: We would rather you ___ the draft again before publishing.", "options": ["reviewed", "reviews", "review", "reviewing"], "answer": "reviewed"},
            {"prompt": "Choose the correct sentence: Seldom ___ such a rapid shift in consumer behavior observed.", "options": ["is", "has", "are", "was"], "answer": "is"},
            {"prompt": "Select the best phrase: The more carefully you plan, the ___ surprises you'll encounter.", "options": ["fewer", "few", "less", "little"], "answer": "fewer"},
        ],
    },
    "C1": {
        "grammar": [
            {"prompt": "Should the board ___ the proposal, the merger will proceed.", "options": ["approve", "approves", "approved", "approving"], "answer": "approve"},
            {"prompt": "The report, portions of which ___ confidential, was circulated internally.", "options": ["remain", "remains", "remaining", "remained"], "answer": "remain"},
            {"prompt": "Only after the audit ___ completed did the investors regain confidence.", "options": ["was", "were", "has", "had"], "answer": "was"},
            {"prompt": "Had the policy been implemented earlier, fewer clients ___ affected.", "options": ["would have been", "will be", "were", "are"], "answer": "would have been"},
            {"prompt": "Were we ___ a larger budget, we could expand internationally.", "options": ["to secure", "securing", "secured", "secure"], "answer": "to secure"},
            {"prompt": "The CEO demanded that every department ___ measurable outcomes.", "options": ["deliver", "delivers", "delivered", "delivering"], "answer": "deliver"},
            {"prompt": "Despite the analysts' predictions, not once ___ the company miss a deadline.", "options": ["did", "does", "had", "has"], "answer": "did"},
            {"prompt": "Were it not for her diplomacy, the negotiations ___ collapsed.", "options": ["might have", "must have", "should have", "will have"], "answer": "might have"},
        ],
        "vocab": [
            {"prompt": "Choose the word that best completes the sentence: The committee praised his ___ leadership style.", "options": ["visionary", "vulnerable", "vacant", "volatile"], "answer": "visionary"},
            {"prompt": "Select the option closest in meaning to 'circumspect'.", "options": ["cautious", "careless", "candid", "casual"], "answer": "cautious"},
            {"prompt": "Which word describes 'a person who supports a cause publicly'?", "options": ["advocate", "adversary", "admirer", "adolescent"], "answer": "advocate"},
            {"prompt": "Choose the best replacement for 'ubiquitous' in the sentence 'Mobile payments are becoming ubiquitous'.", "options": ["commonplace", "costly", "coarse", "convoluted"], "answer": "commonplace"},
            {"prompt": "Pick the word that means 'to make something clearer or easier to understand'.", "options": ["elucidate", "eliminate", "elevate", "emulate"], "answer": "elucidate"},
            {"prompt": "Find the option that means 'showing great attention to detail or correct behavior'.", "options": ["scrupulous", "spontaneous", "speculative", "subtle"], "answer": "scrupulous"},
            {"prompt": "Choose the best synonym for 'resilient'.", "options": ["robust", "redundant", "reluctant", "resistant"], "answer": "robust"},
            {"prompt": "Select the word meaning 'to publicly support a particular policy or idea'.", "options": ["champion", "challenge", "chastise", "channel"], "answer": "champion"},
        ],
        "reading": [
            {"prompt": "Read: 'The white paper argues that regulating artificial intelligence requires cross-border consensus and adaptive frameworks.' What does the white paper argue?", "options": ["AI regulation needs cross-border consensus", "AI should be banned entirely", "AI is cheaper than robotics", "AI has no ethical issues"], "answer": "AI regulation needs cross-border consensus"},
            {"prompt": "Read: 'Having synthesized decades of climate data, the panel advocated immediate investment in resilient infrastructure.' What did the panel advocate?", "options": ["Immediate investment in resilient infrastructure", "Cuts to energy research", "Delayed spending", "Privatizing transport"], "answer": "Immediate investment in resilient infrastructure"},
            {"prompt": "Read: 'The editorial juxtaposes historical context with current policy debates to illuminate systemic biases.' What technique does the editorial use?", "options": ["Juxtaposing history with current debates", "Avoiding historical references", "Focusing solely on data", "Highlighting personal anecdotes"], "answer": "Juxtaposing history with current debates"},
            {"prompt": "Read: 'Because the startup scaled responsibly, it preserved culture while doubling revenue annually.' What was the result of scaling responsibly?", "options": ["The company preserved culture while doubling revenue", "The company reduced staff", "The company delayed expansion", "The company closed offices"], "answer": "The company preserved culture while doubling revenue"},
            {"prompt": "Read: 'The researcher contends that inclusive teams outperform homogeneous groups over time.' What is the researcher's claim?", "options": ["Inclusive teams outperform homogeneous groups", "Homogeneous groups innovate more", "Teams should avoid diversity", "Leaders must centralize power"], "answer": "Inclusive teams outperform homogeneous groups"},
            {"prompt": "Read: 'After scrutinizing the methodology, reviewers deemed the findings provisional pending replication.' How did reviewers describe the findings?", "options": ["Provisional pending replication", "Conclusive and final", "Irrelevant", "Unethical"], "answer": "Provisional pending replication"},
            {"prompt": "Read: 'The documentary interrogates supply chains to expose labor violations otherwise hidden from consumers.' What does the documentary investigate?", "options": ["Supply chains to expose labor violations", "Consumer privacy", "Wildlife conservation", "Sports governance"], "answer": "Supply chains to expose labor violations"},
            {"prompt": "Read: 'Because the nonprofit leverages open data, its reports withstand rigorous peer review.' Why do the nonprofit's reports withstand review?", "options": ["They leverage open data", "They keep data private", "They publish anonymously", "They avoid statistics"], "answer": "They leverage open data"},
        ],
        "use_of_english": [
            {"prompt": "Choose the correct phrase: The initiative is contingent ___ securing stakeholder alignment.", "options": ["upon", "about", "across", "within"], "answer": "upon"},
            {"prompt": "Select the correct word: Little ___ the consultants anticipate such rapid regulatory changes.", "options": ["did", "do", "have", "are"], "answer": "did"},
            {"prompt": "Pick the best option: Were the negotiations to fail, we ___ alternative funding sources.", "options": ["would pursue", "pursue", "will pursue", "pursued"], "answer": "would pursue"},
            {"prompt": "Choose the correct completion: Scarcely had the keynote ended ___ the questions began flooding in.", "options": ["when", "than", "before", "after"], "answer": "when"},
            {"prompt": "Select the correct collocation: They reached consensus ___ a series of facilitated workshops.", "options": ["through", "at", "under", "onto"], "answer": "through"},
            {"prompt": "Pick the right option: The chair requested that all remarks ___ confined to three minutes.", "options": ["be", "are", "were", "being"], "answer": "be"},
            {"prompt": "Choose the correct sentence: Rarely ___ such an eloquent defense of the policy heard.", "options": ["is", "has", "are", "was"], "answer": "is"},
            {"prompt": "Select the best phrase: The more transparently we communicate, the ___ stakeholders trust our decisions.", "options": ["more", "most", "many", "much"], "answer": "more"},
        ],
    },
    "C2": {
        "grammar": [
            {"prompt": "Were the data ___ more robust, the hypothesis might withstand scrutiny.", "options": ["to be", "been", "being", "be"], "answer": "to be"},
            {"prompt": "At no point ___ the board concede that the forecasts were flawed.", "options": ["did", "has", "had", "was"], "answer": "did"},
            {"prompt": "The report recommended that funding ___ contingent upon verified outcomes.", "options": ["remain", "remained", "remains", "remaining"], "answer": "remain"},
            {"prompt": "Should the legislation ___ enacted, multinational firms will reassess their strategies.", "options": ["be", "being", "been", "to be"], "answer": "be"},
            {"prompt": "Little ___ the researchers anticipate the paradigm shift their study would trigger.", "options": ["did", "do", "have", "are"], "answer": "did"},
            {"prompt": "Not until the transcripts ___ digitized were they made publicly accessible.", "options": ["were", "are", "have", "had"], "answer": "were"},
            {"prompt": "Were it not for the whistleblower, the malpractice ___ undiscovered.", "options": ["would have gone", "will go", "has gone", "is going"], "answer": "would have gone"},
            {"prompt": "Had the guidelines been interpreted narrowly, several stakeholders ___ excluded.", "options": ["would have been", "were", "are", "will be"], "answer": "would have been"},
        ],
        "vocab": [
            {"prompt": "Choose the word that best completes the sentence: The philosopher's arguments were grounded in a ___ understanding of ethics.", "options": ["nuanced", "naive", "narrow", "nominal"], "answer": "nuanced"},
            {"prompt": "Select the option closest in meaning to 'equivocate'.", "options": ["prevaricate", "pronounce", "persevere", "perturb"], "answer": "prevaricate"},
            {"prompt": "Which word describes 'a leader who exercises absolute power often cruelly'?", "options": ["despot", "delegate", "deacon", "debutant"], "answer": "despot"},
            {"prompt": "Choose the best replacement for 'esoteric' in the sentence 'The lecture explored esoteric legal doctrines'.", "options": ["arcane", "artful", "arbitrary", "articulate"], "answer": "arcane"},
            {"prompt": "Pick the word that means 'to formally cancel or reverse a decision'.", "options": ["rescind", "resist", "relish", "recount"], "answer": "rescind"},
            {"prompt": "Find the option that means 'expressing sorrow or remorse'.", "options": ["contrite", "cohesive", "concise", "contiguous"], "answer": "contrite"},
            {"prompt": "Choose the best synonym for 'perspicacious'.", "options": ["astute", "apathetic", "amiable", "abrupt"], "answer": "astute"},
            {"prompt": "Select the word meaning 'to publicly denounce or condemn'.", "options": ["decry", "defer", "deplete", "devalue"], "answer": "decry"},
        ],
        "reading": [
            {"prompt": "Read: 'The investigative series indicts opaque procurement practices that facilitate systemic corruption across public agencies.' What does the series indict?", "options": ["Opaque procurement practices", "Transparent budgeting", "Private philanthropy", "Global supply chains"], "answer": "Opaque procurement practices"},
            {"prompt": "Read: 'By tracing the jurisprudence, the scholar elucidates how precedent constrains judicial discretion.' What does the scholar elucidate?", "options": ["How precedent constrains judicial discretion", "Why courts ignore evidence", "How juries are selected", "Why legislation is delayed"], "answer": "How precedent constrains judicial discretion"},
            {"prompt": "Read: 'The commission's dossier interweaves forensic audits with whistleblower testimony to substantiate its allegations.' How does the dossier substantiate its allegations?", "options": ["By combining forensic audits with whistleblower testimony", "By relying on anonymous blogs", "By summarizing press releases", "By citing unrelated statistics"], "answer": "By combining forensic audits with whistleblower testimony"},
            {"prompt": "Read: 'Because the treaty eschews punitive measures, it relies on voluntary compliance and peer accountability.' What does the treaty rely on?", "options": ["Voluntary compliance and peer accountability", "Strict sanctions", "Financial penalties", "Military enforcement"], "answer": "Voluntary compliance and peer accountability"},
            {"prompt": "Read: 'The panel contends that algorithmic opacity perpetuates inequity in credit scoring.' What is the panel's contention?", "options": ["Algorithmic opacity perpetuates inequity", "Manual reviews are obsolete", "Credit demand is falling", "Regulators overreach"], "answer": "Algorithmic opacity perpetuates inequity"},
            {"prompt": "Read: 'Having synthesized multilingual testimonies, the report delineates a blueprint for transitional justice.' What does the report delineate?", "options": ["A blueprint for transitional justice", "A plan for infrastructure", "A guide to tax reform", "A manual for software"], "answer": "A blueprint for transitional justice"},
            {"prompt": "Read: 'The thesis interrogates how philanthropic capital can catalyze civic innovation without entrenching elite control.' What does the thesis interrogate?", "options": ["How philanthropic capital can catalyze civic innovation", "How cities fund roads", "Why taxes remain high", "Why elections are delayed"], "answer": "How philanthropic capital can catalyze civic innovation"},
            {"prompt": "Read: 'Because the nonprofit publishes its methodology, external evaluators corroborate its impact assessments.' What enables evaluators to corroborate the assessments?", "options": ["Publishing the methodology", "Lobbying politicians", "Limiting field visits", "Reducing sample sizes"], "answer": "Publishing the methodology"},
        ],
        "use_of_english": [
            {"prompt": "Choose the correct phrase: The policy hinges ___ whether regulators embrace interoperable standards.", "options": ["on", "in", "with", "by"], "answer": "on"},
            {"prompt": "Select the correct word: Rarely ___ policymakers confront such multifaceted dilemmas with unanimity.", "options": ["do", "have", "had", "are"], "answer": "do"},
            {"prompt": "Pick the best option: The tribunal ordered that all evidence ___ disclosed to the defense immediately.", "options": ["be", "is", "was", "being"], "answer": "be"},
            {"prompt": "Choose the correct completion: No sooner had the ruling been announced ___ investors reacted nervously.", "options": ["than", "when", "before", "after"], "answer": "than"},
            {"prompt": "Select the correct collocation: The initiative seeks to hold corporations ___ meaningful transparency benchmarks.", "options": ["to", "for", "at", "over"], "answer": "to"},
            {"prompt": "Pick the right option: The chair insisted that dissenting opinions ___ archived alongside the final report.", "options": ["be", "are", "were", "being"], "answer": "be"},
            {"prompt": "Choose the correct sentence: Hardly ___ a precedent as consequential as this one.", "options": ["has there been", "there has", "had there been", "there having been"], "answer": "has there been"},
            {"prompt": "Select the best phrase: The more stringently we audit, the ___ anomalies we overlook.", "options": ["fewer", "less", "few", "little"], "answer": "fewer"},
        ],
    },
}

skill_codes = {"grammar": "GR", "vocab": "VO", "reading": "RD", "use_of_english": "UE"}

result = {}
for level, skills in level_data.items():
    level_items = []
    counters = {skill: 1 for skill in skills}
    for skill, items in skills.items():
        for item in items:
            idx = counters[skill]
            counters[skill] += 1
            entry = {
                "id": f"{level}-{skill_codes[skill]}-{idx:03d}",
                "level": level,
                "skill": skill,
                "type": "multiple_choice",
                **item,
            }
            level_items.append(entry)
    result[level] = level_items

path = Path(__file__).resolve().parents[1] / "english_test_items_v1.json"
path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(f"Wrote {path}")
