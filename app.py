import streamlit as st
import base64
import os

# 1. 網頁基本設定
st.set_page_config(page_title="2D 情感數位學習助理", layout="wide")

st.title("🎭 2D 情感數位學習助理 ")

# 2. 檢查與載入 2D 圖片
IMG_CLOSED = "mouth-closed.png"
IMG_OPEN = "mouth-open.png"

if not os.path.exists(IMG_CLOSED) or not os.path.exists(IMG_OPEN):
    st.error("❌ 找不到圖片檔案！請確保 'mouth-closed.png' 和 'mouth-open.png' 放在與 app.py 相同的資料夾。")

def load_image_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

img_closed_b64 = load_image_base64(IMG_CLOSED)
img_open_b64 = load_image_base64(IMG_OPEN)

# 3. 建立 Streamlit 左右兩欄 UI 佈局
col1, col2 = st.columns([1, 1.4])

with col2:
    st.subheader("📝 內容輸入與上傳 (Content Input & Upload)")
    
    # 同學可直接拖曳上傳 .txt 檔案
    uploaded_file = st.file_uploader("📁 上傳學生的文字檔 (.txt)", type=["txt"])
    
    # 決定編輯框的預設顯示內容
    if uploaded_file is not None:
        try:
            default_text = uploaded_file.read().decode("utf-8")
        except:
            default_text = "檔案讀取失敗，請確保是 UTF-8 編碼的 .txt 檔案。"
    else:
        default_text = ""
        
    # 文字編輯區
    student_text = st.text_area("內容框 (可直接在此修改文字)", value=default_text, height=140)
    
    st.write("⚙️ 語音與情感設定 (Voice Settings)")
    inner_col1, inner_col2 = st.columns(2)
    
    with inner_col1:
        # 切換語言/口音
        language_option = st.selectbox(
            "切換語言/口音 (Language/Accent)", 
            ["廣東話 (Cantonese)", "普通話 (Mandarin)", "美式英語 (US Accent)", "英式英語 (UK Accent)"]
        )
        if "US" in language_option:
            lang_code = "en-US"
        elif "UK" in language_option:
            lang_code = "en-GB"
        elif "普通話" in language_option:
            lang_code = "zh-CN"
        else:
            lang_code = "zh-HK"   # 正宗香港廣東話

    with inner_col2:
        # 情感選擇
        emotion_option = st.selectbox(
            "選擇助理當前情緒 (Choose Emotion)",
            ["😊 親切溫柔 (Friendly)", "😢 傷心失落 (Sad)"]
        )
        
        # 依據情緒調整背景色、音調 (Pitch) 與對嘴速度
        if "親切" in emotion_option:
            bg_gradient = "linear-gradient(145deg, #e0e7ff, #f1f5f9)" 
            pitch = 1.0       # 正常音調
            base_delay = 110  # 毫秒
            emotion_speed_mod = 0.0  
       
        else:
            bg_gradient = "linear-gradient(145deg, #e2e8f0, #cbd5e1)" 
            pitch = 0.7       # 音調低沉，顯得悲傷
            base_delay = 160  # 嘴巴動得慢
            emotion_speed_mod = -0.25 # 語速變慢

    # 語速基礎滑桿
    speed = st.slider("調整基礎語速 (Speed Slider)", min_value=0.5, max_value=1.5, value=1.0, step=0.1)
    final_speed = max(0.5, min(2.0, speed + emotion_speed_mod))

# 4. 透過一個隱藏的網頁元件，將文字、音調、語速直接傳遞給前端瀏覽器
# 100% 繞過 Python 後端與微軟伺服器，由前端原生 JavaScript 直接處理對嘴動畫
import streamlit.components.v1 as components

# 清理換行與特殊字符以防 JS 語法崩潰
safe_text = student_text.replace('`','\\`').replace('\n',' ').replace('\r',' ')

html_code = f"""
<div style="display: flex; justify-content: center; align-items: flex-end; height: 380px; background: {bg_gradient}; border-radius: 20px; overflow: hidden; border: 1px solid rgba(79, 70, 229, 0.1); transition: background 0.5s ease;">
    <img id="avatar" src="data:image/png;base64,{img_closed_b64}" style="height: 95%; width: auto; object-fit: contain;">
</div>

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px;">
    <button id="js-speak" style="background-color: #4f46e5; color: white; border: none; padding: 12px; font-size: 15px; font-weight: bold; border-radius: 10px; cursor: pointer;">🔊 開始朗讀 (Speak)</button>
    <button id="js-stop" style="background-color: #ef4444; color: white; border: none; padding: 12px; font-size: 15px; font-weight: bold; border-radius: 10px; cursor: pointer;">🛑 停止 (Stop)</button>
</div>

<script>
    let animationFrameId = null;
    const imgClosed = "data:image/png;base64,{img_closed_b64}";
    const imgOpen = "data:image/png;base64,{img_open_b64}";
    const avatar = document.getElementById('avatar');

    document.getElementById('js-speak').addEventListener('click', () => {{
        window.speechSynthesis.cancel();
        if (animationFrameId) clearTimeout(animationFrameId);

        const utterance = new SpeechSynthesisUtterance(`{safe_text}`);
        utterance.lang = '{lang_code}';
        utterance.rate = {final_speed};
        utterance.pitch = {pitch};

        utterance.onstart = () => {{
            updateMouth();
        }};
        utterance.onend = () => {{ resetAvatar(); }};
        utterance.onerror = () => {{ resetAvatar(); }};

        window.speechSynthesis.speak(utterance);
    }});

    document.getElementById('js-stop').addEventListener('click', () => {{
        window.speechSynthesis.cancel();
        resetAvatar();
    }});

    function updateMouth() {{
        if (window.speechSynthesis.speaking) {{
            const shouldOpen = Math.random() > 0.4;
            avatar.src = shouldOpen ? imgOpen : imgClosed;
            animationFrameId = setTimeout(() => {{
                requestAnimationFrame(updateMouth);
            }}, {base_delay});
        }} else {{
            resetAvatar();
        }}
    }}

    function resetAvatar() {{
        if (animationFrameId) clearTimeout(animationFrameId);
        avatar.src = imgClosed;
    }}
</script>
"""

with col1:
    st.subheader("AI 助理表情 (Assistant Emotion)")
    components.html(html_code, height=460)









