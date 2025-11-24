import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid

# --- AYARLAR VE KURULUM ---
st.set_page_config(page_title="Terapist Asistanı", page_icon="🧠", layout="centered")

# Veri Saklama (Session State - Tarayıcı kapanana kadar veriyi tutar)
# Not: Gerçek bir uygulamada burası bir Veritabanına (SQLite/PostgreSQL) bağlanmalıdır.
if 'sessions' not in st.session_state:
    st.session_state.sessions = []

# --- FONKSİYONLAR ---

def add_session(client_name, session_name, date, time, fee, phone, email):
    new_session = {
        "id": str(uuid.uuid4()),
        "client_name": client_name,
        "session_name": session_name,
        "date": date,
        "time": time,
        "fee": fee,
        "phone": phone,
        "email": email,
        "notes": "",
        "completed": False,
        "paid": False
    }
    st.session_state.sessions.append(new_session)

def get_whatsapp_link(phone, message):
    # Telefon numarasındaki boşlukları ve karakterleri temizle
    clean_phone = ''.join(filter(str.isdigit, phone))
    return f"https://wa.me/{clean_phone}?text={message}"

# --- ARAYÜZ TASARIMI ---

st.title("🧠 Terapist Asistanı")
st.markdown("---")

# Yan Menü (Navigasyon)
menu = st.sidebar.radio("Menü", ["Randevu Takvimi", "Yeni Seans Ekle", "Finansal Durum"])

# --- 1. YENİ SEANS EKLEME ---
if menu == "Yeni Seans Ekle":
    st.header("Yeni Seans Oluştur")
    
    with st.form("new_session_form"):
        c_name = st.text_input("Danışan Adı Soyadı")
        s_name = st.text_input("Seans Başlığı/Türü (Örn: BDT, İlk Görüşme)")
        col1, col2 = st.columns(2)
        with col1:
            s_date = st.date_input("Tarih", min_value=datetime.today())
        with col2:
            s_time = st.time_input("Saat")
        
        s_fee = st.number_input("Seans Ücreti (TL)", min_value=0, step=100)
        s_phone = st.text_input("Telefon (905...)", help="WhatsApp hatırlatması için gereklidir.")
        s_email = st.text_input("E-posta Adresi")
        
        submitted = st.form_submit_button("Seansı Kaydet")
        
        if submitted:
            if c_name and s_date:
                add_session(c_name, s_name, s_date, s_time, s_fee, s_phone, s_email)
                st.success(f"{c_name} için seans oluşturuldu!")
            else:
                st.error("Lütfen en azından isim ve tarih giriniz.")

# --- 2. RANDEVU TAKVİMİ VE LİSTESİ ---
elif menu == "Randevu Takvimi":
    st.header("📅 Yaklaşan Seanslar")
    
    if not st.session_state.sessions:
        st.info("Henüz planlanmış bir seans yok.")
    else:
        # Tarihe göre sırala
        sorted_sessions = sorted(st.session_state.sessions, key=lambda x: (x['date'], x['time']))
        
        for session in sorted_sessions:
            with st.expander(f"{session['date']} - {session['time']} | {session['client_name']} ({session['session_name']})"):
                
                # Detaylar
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Danışan:** {session['client_name']}")
                    st.write(f"**İletişim:** {session['phone']}")
                    st.write(f"**Ücret:** {session['fee']} TL")
                    
                    # Ödeme Durumu
                    is_paid = st.checkbox("Ödeme Alındı", value=session['paid'], key=f"paid_{session['id']}")
                    session['paid'] = is_paid
                
                with col2:
                    # Hatırlatma Butonları
                    msg = f"Merhaba Sayın {session['client_name']}, {session['date']} tarihinde saat {session['time']} randevunuzu hatırlatmak isteriz."
                    wa_link = get_whatsapp_link(session['phone'], msg)
                    st.markdown(f"[📱 WhatsApp Hatırlatması Gönder]({wa_link})", unsafe_allow_html=True)
                    st.caption("*Linke tıkladığınızda WhatsApp açılır ve mesaj hazır gelir.*")

                st.markdown("---")
                # Notlar Alanı
                st.write("**Seans Notları:**")
                notes = st.text_area("Notlarınızı buraya girin...", value=session['notes'], key=f"note_{session['id']}")
                session['notes'] = notes # Notları anlık güncelle

# --- 3. FİNANSAL DURUM ---
elif menu == "Finansal Durum":
    st.header("💰 Gelir Takibi")
    
    if not st.session_state.sessions:
        st.warning("Hesaplama için veri yok.")
    else:
        df = pd.DataFrame(st.session_state.sessions)
        
        total_potential = df['fee'].sum()
        total_received = df[df['paid'] == True]['fee'].sum()
        pending = total_potential - total_received
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam Beklenen", f"{total_potential} TL")
        col2.metric("Tahsil Edilen", f"{total_received} TL", delta=f"{total_received} TL")
        col3.metric("Bekleyen Ödeme", f"{pending} TL", delta=f"-{pending} TL", delta_color="inverse")
        
        st.markdown("### Seans Geçmişi Tablosu")
        st.dataframe(df[['date', 'client_name', 'fee', 'paid', 'notes']])
