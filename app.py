import streamlit as st
import requests
import json
import google.generativeai as genai

# הגדרות דף
st.set_page_config(page_title="סוכן כוונת רכישה - משכנתאות", page_icon="🏠", layout="wide")

# עיצוב RTL (ימין-לשמאל) מותאם אישית
# עיצוב RTL (ימין-לשמאל) מוחלט ואגרסיבי
st.markdown("""
<style>
    /* הפיכת כל האפליקציה מימין-לשמאל, כולל Flexbox וכל שכבת בלוק */
    .stApp, .main, .block-container, div[data-testid="stAppViewContainer"], div[data-testid="stSidebar"] {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* סידור פנימי של עמודות, כפתורים ותיבות תחת Flexbox (למשל סרגל הצד ואזור התוכן) */
    div.row-widget.stButton > button, div[data-testid="stFormSubmitButton"] > button {
        float: right !important;
    }
    
    div[data-testid="stVerticalBlock"], div[data-testid="stHorizontalBlock"] {
        direction: rtl !important;
        align-items: flex-start !important;
    }

    /* שדות טקסט והתוויות שלהם */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, div[data-testid="stTextInput"] label, div[data-testid="stTextArea"] label {
        direction: rtl !important;
        text-align: right !important;
        float: right !important;
        width: 100% !important;
    }
    
    /* יישור טקסט רגיל, כותרות, בלוקים והודעות מערכת - דריסת מרקרים של Streamlit */
    p, h1, h2, h3, h4, h5, h6, li, span, div.stMarkdown, div[data-testid="stMarkdownContainer"], .element-container {
        text-align: right !important;
        direction: rtl !important;
        font-family: 'Assistant', 'Heebo', 'Rubik', sans-serif !important;
    }
    
    /* תפריט צדדי (Sidebar) - יישור מלא */
    section[data-testid="stSidebar"] {
        direction: rtl !important;
        text-align: right !important;
    }
    
    section[data-testid="stSidebar"] > div {
        direction: rtl !important;
    }
    
    /* כפתורים ותיבות התראה (Success, Info, Warning, Error) */
    div[data-testid="stAlert"] {
        direction: rtl !important;
        text-align: right !important;
    }
    
    div[data-testid="stAlert"] > div {
        direction: rtl !important;
        justify-content: right !important;
        text-align: right !important;
    }
    
    /* עיצוב כללי של חלונית העליונה */
    .css-1544g2n {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏠 סוכן איתור קהלי יעד וכוונת רכישה")
st.markdown("הכנס מילת מפתח מתחום המשכנתאות (לדוגמה: *משכנתא פנסיונית*), והמערכת תנתח את תוצאות החיפוש בגוגל ותמליץ לך על **קהלי יעד משתלמים יותר** (אוקיינוס כחול) והשאלות שהם שואלים עכשיו.")

# סרגל צד לצורך הכנסת המפתחות
with st.sidebar:
    st.header("הגדרות חיבור (API Keys)")
    st.markdown("כדי שהמערכת תעבוד, יש להזין את המפתחות שייצרתם:")
    gemini_key = st.text_input("מפתח Gemini (גוגל)", type="password")
    serper_key = st.text_input("מפתח Serper (חיפוש)", type="password")
    
    st.markdown("---")
    st.markdown("**אין לכם מפתחות? קחו בחינם:**")
    st.markdown("1. [לחצו כאן להוצאת מפתח Gemini](https://aistudio.google.com/app/apikey)")
    st.markdown("2. [לחצו כאן להוצאת מפתח Serper](https://serper.dev/)")

# שדה קלט מרכזי
keyword = st.text_input("🔍 הקלד נושא מאמר או מילת מפתח (למשל: מימון לדיור, סילוק משכנתא):")
analyze_button = st.button("🚀 נתח קהל יעד ומצא הזדמנויות", type="primary")

# פונקציה לחיפוש בגוגל דרך Serper
def search_google(query, api_key):
    url = "https://google.serper.dev/search"
    payload = json.dumps({
      "q": query,
      "gl": "il",  # ישראל
      "hl": "iw",  # עברית
      "num": 20    # הגדלנו ל-20 תוצאות כדי לאפשר מחקר עומק
    })
    headers = {
      'X-API-KEY': api_key,
      'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()

# פונקציה לניתוח בינה מלאכותית דרך Gemini עם מנגנון גיבוי אוטומטי
def analyze_intent_with_gemini(search_data, keyword, api_key):
    genai.configure(api_key=api_key)
    
    # רשימת מודלים לניסיון בסדר עדיפות
    models_to_try = [
        'gemini-2.0-flash-lite',
        'gemini-1.5-flash',
        'gemini-flash-latest',
        'gemini-2.0-flash',
        'gemini-pro-latest'
    ]
    
    organic = search_data.get("organic", [])
    paa = search_data.get("peopleAlsoAsk", [])
    related = search_data.get("relatedSearches", [])
    
    # בניית ההקשר עבור המודל על בסיס נתוני החיפוש האמיתיים
    context = f"Keyword searched: {keyword}\n\n"
    context += "Organic Results (Top 15-20 Google IL):\n"
    for r in organic:
        context += f"- Title: {r.get('title')}\n  Snippet: {r.get('snippet')}\n  Link: {r.get('link')}\n"
    
    if paa:
        context += "\nPeople Also Ask (Questions from Google):\n"
        for p in paa:
            context += f"- {p.get('question')}\n"
            
    if related:
        context += "\nRelated Searches (Autocompletes/Related):\n"
        for r in related:
            context += f"- {r.get('query')}\n"

    prompt = f"""
# Role & Objective
אתה אנליסט שוק ומומחה Buyer Psychology אובייקטיבי ברמת Master. 
המשימה שלך: לבצע מחקר שטח רחב על תחום ייעוץ המשכנתאות בישראל כדי לזהות את כל קהלי היעד הרלוונטיים למילת המפתח: "{keyword}". 

**כלל ברזל:** אל תסתמך רק על ידע כללי; השתמש בנתוני ה-SERP (תוצאות החיפוש) המצורפים מטה כבסיס מחקרי חי כדי למנוע הטיה (Bias) ולהבטיח ניתוח אובייקטיבי המבוסס על מה שקורה בשוק עכשיו.

---

# נתוני מחקר שטח (SERP Data)
להלן הנתונים הגולמיים שנסרקו עבורך (מאמרים מובילים, שאלות נפוצות וחיפושים קשורים):
{context}

---

# Phase 1 — מחקר שטח חי (Mandatory)
1. **סריקת שוק רחבה (Deep Research):** נתח את תוצאות החיפוש שסופקו לך (לפחות 15 מאמרים מובילים). 
   מטרת הסריקה: להבין אילו קהלים קיימים בשוק, מהן החרדות העדכניות, ומהן הזוויות שהמתחרים תוקפים.
2. **קליטת מילת המפתח:** נתח את השאילתה "{keyword}" כנקודת מוצא, אך הצלב אותה מול תמונת השוק המלאה בנתונים לעיל.

---

# Phase 2 — ניתוח פערים והזדמנויות (Market Context)
השוואת השאילתה לתוצאות ה-SERP:
- **מה חסר?** זהה נושאים או חרדות שמופיעים בתוצאות החיפוש אך דורשים העמקה נוספת.
- **זיהוי הטיה (Bias Detection):** האם השוק כרגע "נעול" על קהל מסוים ומתעלם מפוטנציאל רווחי אחר?
- **SGE/GEO Gap:** זהה איפה מאמר חדש יכול לתת "Information Gain" (ערך מוסף חדש) מעבר למה שגוגל כבר מציג ב-Snippets.

---

# Phase 3 — מיפוי Buyer Psychology אובייקטיבי
## צעד א — זיהוי Journey_Type
בחר את סוג המסע הרלוונטי ביותר: ACQUISITION (רכישה) / REFINANCING (מחזור) / REVERSE (הפוכה) / ADVISORY (ייעוץ כללי).

## צעד ב — רשימת קהלים מלאה
מפה בראשך 4-5 קהלים שונים שעולים מהנתונים.

## צעד ג — בחירת שני קהלי ה"זהב"
בחר את שני הקהלים בעלי כוונת הרכישה הגבוהה ביותר בשוק כיום (אלו שמוכנים להשאיר ליד/לקבוע ייעוץ).

---

# Phase 4 — ניתוח 3 השכבות
עבור השאילתה המרכזית, זהה:
- שכבה 1: מה נאמר (הטקסט של השאילתה).
- שכבה 2: מה המטרה (הצורך הרציונלי).
- שכבה 3: מה המניע (הפחד/החלום העמוק).

---

# Phase 5 — פלט מובנה לאוטומציה (Output)
הדפס את התוצאה במבנה זה בלבד (בעברית), ללא טקסט חופשי:

[MARKET_INTELLIGENCE]
- מקורות סריקה: [SOURCE: DEEP_RESEARCH + 15_SITES_ANALYZED]
- ניתוח הטיה: [האם השוק כרגע מוטה? מה הוא מפספס?]
- פער GEO קריטי: [מה המידע שחסר בגוגל כיום כדי לנצח את ה-AI בתשובה למשתמש]

[DATA_NODE_CONTEXT]
- Journey_Type: [סוג המסע]
- מילת מפתח ראשית: [הביטוי]
- שכבה 1 (מילולי): [מה הוקלד]
- שכבה 2 (רציונלי): [מה מחפשים מעשית]
- שכבה 3 (רגשי): [מה עובר להם בראש]

[AUDIENCE_1] & [AUDIENCE_2] (עבור כל קהל בנפרד):
- פרופיל: [תיאור מצב חיים ונסיבות]
- מניע רגשי עמוק: [החלום / הלחץ / החשש]
- JTBD: ["כש... אני רוצה... כדי ש..."]
- Friction: [מה מעכב אותם]
- Catalyst: [מה יגרום להם לפעול עכשיו]
- כוונת רכישה: [1-10]
- [Cialdini_Lever]: [Authority / Social Proof / Scarcity / Consistency - ואיך ליישם במשפט]
- [Fogg_B_Score]: [הערכת B=MAP וסוג ה-Prompt הנדרש: Spark / Facilitator / Signal]
    """
    
    last_error = ""
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and hasattr(response, 'text'):
                return response.text
        except Exception as e:
            last_error = str(e)
            continue
            
    return f"שגיאה בהפעלת הבינה המלאכותית: לאחר מספר ניסיונות עם מודלים שונים, המכסה של גוגל עדיין מלאה. אנא המתן דקה ונסה שוב. (שגיאה אחרונה: {last_error})"

# לוגיקת האפליקציה בעת לחיצה על הכפתור
if analyze_button:
    if not gemini_key or not serper_key:
        st.warning("⚠️ לא ניתן להפעיל: אנא הקלד/הדבק את מפתחות ה-API בסרגל הצד (שמאל) כדי להתחיל בניתוח.")
    elif not keyword:
        st.warning("אנא הזן מילת מפתח או נושא לניתוח בתיבת הטקסט.")
    else:
        # שלב 1: חיפוש בגוגל
        with st.spinner("סורק את תוצאות גוגל ישראל ואוסף נתונים (Serper API)..."):
            try:
                search_results = search_google(keyword, serper_key)
                if "organic" not in search_results:
                    st.error("הייתה שגיאה באיסוף הנתונים מגוגל. אנא ודא שמפתח ה-Serper תקין ושלא חרגת ממכסת החיפושים.")
                    st.stop()
            except Exception as e:
                st.error(f"שגיאת תקשורת עם Serper API: {e}")
                st.stop()
                
        # שלב 2: ניתוח ג'מיני
        with st.spinner("מפענח את הפסיכולוגיה הצרכנית ומייצר קהלי יעד חלופיים משתלמים (Gemini AI)..."):
            try:
                analysis = analyze_intent_with_gemini(search_results, keyword, gemini_key)
                st.success("✅ הניתוח הושלם בהצלחה!")
                st.markdown("---")
                
                # הצגת התשובה המלאה
                st.markdown(analysis)
                
            except Exception as e:
                st.error(f"שגיאת תקשורת עם Gemini API: {e}")
                st.info("טיפ למפתח: ודא שמפתח ה-Gemini תקף ופתוח לשימוש בישראל.")
