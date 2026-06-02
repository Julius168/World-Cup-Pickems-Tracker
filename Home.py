import streamlit as st
 
st.set_page_config(
    page_title="World Cup",
    page_icon="🏆",
    layout="wide",
)
 
st.markdown("""
    <style>
        @import url('https://fonts.cdnfonts.com/css/bebas-neue');
 
        [data-testid="stAppViewContainer"] {
            background-color: #0a1628;
        }
 
        [data-testid="stSidebar"] {
            background-color: #071020;
        }

        [data-testid="stSidebar"] span {
            color: white !important;
            font-size: 16px;
            letter-spacing: 1px;
        }

        [data-testid="stSidebar"] li:hover span {
            color: #FFD23F !important;
        }

        [data-testid="stSidebar"] li[aria-selected="true"] span {
            color: #FFD23F !important;
        }

        [data-testid="stSidebar"] li[aria-selected="true"] {
            background-color: rgba(255, 210, 63, 0.15);
            border-radius: 8px;
        }
        .main-title {
            font-family: 'Bebas Neue', sans-serif;
            font-size: 100px;
            letter-spacing: 6px;
            color: #FFD23F !important;
            text-align: center;
            margin-top: 80px;
        }
 
        .sub-title {
            text-align: center;
            color: rgba(255,255,255,0.5);
            font-size: 18px;
            letter-spacing: 6px;
            text-transform: uppercase;
        }
 
        .trophy {
            text-align: center;
            font-size: 80px;
            margin-top: 60px;
        }
    </style>
""", unsafe_allow_html=True)
 
st.markdown('<div class="trophy">🏆</div>', unsafe_allow_html=True)
st.markdown('<h1 class="main-title">World Cup</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Pick\'em Competition</p>', unsafe_allow_html=True)