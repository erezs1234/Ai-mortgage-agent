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
      "hl": "iw"   # עברית
    })
    headers = {
      'X-API-KEY': api_key,
      'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()

# פונקציה לניתוח בינה מלאכותית דרך Gemini
def analyze_intent_with_gemini(search_data, keyword, api_key):
    genai.configure(api_key=api_key)
    # נשתמש בגרסה העדכנית ביותר של ג'מיני 1.5 שכבר פתוחה לחלוטין לכולם בישראל
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    
    organic = search_data.get("organic", [])
    paa = search_data.get("peopleAlsoAsk", [])
    related = search_data.get("relatedSearches", [])
    
    context = f"Keyword searched: {keyword}\n\n"
    context += "Organic Results (Top 10 Google IL):\n"
    for r in organic[:10]:
        context += f"- Title: {r.get('title')}\n  Snippet: {r.get('snippet')}\n"
    
    if paa:
        context += "\nPeople Also Ask (Questions from Google):\n"
        for p in paa:
            context += f"- {p.get('question')}\n"
            
    if related:
        context += "\nRelated Searches (Autocompletes/Related):\n"
        for r in related:
            context += f"- {r.get('query')}\n"

    prompt = f"""
    אתה יועץ שיווקי בכיר ופסיכולוג צרכנים בישראל, מומחה בתחום המשכנתאות והמימון (כגון משכנתא הפוכה, משכנתא לדירה ראשונה, מימון לדיור, פנסיונית).
    אני מספק לך נתונים שנאספו מ-10 התוצאות הראשונות בגוגל ישראל, כולל "אנשים שאלו גם" (PAA) וחיפושים קשורים, עבור מילת המפתח: "{keyword}".
    
    מידע מגוגל:
    {context}
    
    אנא בצע את הניתוח הבא וכתוב אותו בעברית ברורה, מקצועית, שיווקית ומוכוונת פעולה.
    חלק את התשובה שלך ל-3 חלקים בדיוק כפי המופיע מטה, השתמש בכותרות ברורות והדגשות:
    
    ### 📊 חלק 1: הסטטוס קוו (למי כל המתחרים מכוונים כרגע?)
    - מהי כוונת הרכישה (Commercial Intent) הממוצעת של הקהל הנוכחי שמחפש את זה לפי המאמרים (מידע, השוואה, קנייה)?
    - מי הקהל הזה לפי הניתוח של המאמרים? ממה הוא חושש? (האם זהו קהל של מתעניינים בלבד, חוקרים, או קונים בשלים?)
    
    ### 🌊 חלק 2: האוקיינוס הכחול (קהל בשל ורווחי שהמתחרים מפספסים)
    - הצע קהל יעד *אחר* או ממוקד יותר בישראל, שמכוון הרבה יותר לרכישה ולסגירת עסקה בטווח הקצר (למשל, במקום מתעניינים כלליים - משקיעים/ילדים להורים שרוצים אקזיט וכו').
    - נתח מהי הפסיכולוגיה הנסתרת והכאבים העמוקים של הקהל החדש הזה בתחומי המשכנתאות. מה הם באמת רוצים להשיג? (למשל: כבוד מול הבנק, בטחון כלכלי למשפחה, לנצח את השיטה, חרדה קיומית).
    
    ### 🎯 חלק 3: צמתי קבלת החלטות (השאלות של פנקס הצ'קים)
    - ספק רשימה של 6-8 שאלות "Long Tail" (זנב ארוך) בדיוק כפי שהקהל ה*חדש והבשל* הזה יקליד במנועי החיפוש הישראליים או ישאל צ'אטבוטים (כמו ChatGPT/Claude). 
    - אלו חייבות להיות שאלות אנושיות, יומיומיות (עם סלנג אם צריך), שמעידות על מוכנות לקבלת החלטה או הצורך בייעוץ מקצועי עכשיו. (לדוגמה: "איך הבנק לא לוקח להורים את הבית במשכנתא הפוכה?"). ציין עבור כל שאלה מדוע היא מעידה על כוונת רכישה חזקה.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        try:
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
            error_msg = f"שגיאה בהפעלת ג'מיני: {str(e)}\n\n**המודלים הזמינים למפתח שלך הם:**\n" + ", ".join(available_models)
            return error_msg
        except Exception as inner_e:
            return f"שגיאת תקשורת עם אלגוריתם הבינה המלאכותית: {e}"

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
