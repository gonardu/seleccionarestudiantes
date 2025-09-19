import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import random
import json
import os

# ---------- CONFIG ----------
USERS_FILE = "users.json"

# Inicializar JSON de usuarios si no existe
if not os.path.exists(USERS_FILE):
    default_users = {
        "admin": {
            "password": "1234",  # o hash si querés
            "sheet_id": "12BC_5JMZay0ntdmDMUx2eYAQFt-r1d6SoPBIPJOh2EQ"  # hoja por defecto
        }
    }
    with open(USERS_FILE, "w") as f:
        json.dump(default_users, f, indent=4)

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

# ---------- LOGIN ----------
st.title("🔒 Login")
users = load_users()

username_input = st.text_input("Usuario")
password_input = st.text_input("Contraseña", type="password")

if st.button("Ingresar"):
    if username_input in users and users[username_input]["password"] == password_input:
        st.session_state.logged_in = True
        st.session_state.username = username_input
        st.session_state.sheet_id = users[username_input]["sheet_id"]
        st.success(f"Bienvenido, {username_input}!")
    else:
        st.error("Usuario o contraseña incorrectos ❌")

# ---------- SESIÓN INICIADA ----------
if st.session_state.get("logged_in"):

    # ---------- Autenticación Google Sheets ----------
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.session_state.sheet_id).sheet1

    # ---------- Leer alumnos ----------
    alumnos = sheet.col_values(1)[1:]  # saltamos encabezado
    alumnos_text = "\n".join(alumnos)
    new_alumnos = st.text_area("Lista de alumnos (uno por línea)", alumnos_text).splitlines()
    if st.button("Guardar lista"):
        sheet.resize(len(new_alumnos)+1, 1)
        sheet.update("A2:A", [[a] for a in new_alumnos])
        st.success("Lista guardada ✅")

    # ---------- Selección aleatoria ----------
    st.markdown("### 🎯 Selección de alumno")
    if "seleccionado" not in st.session_state:
        st.session_state.seleccionado = None

    if st.button("Seleccionar alumno"):
        if new_alumnos:
            st.session_state.seleccionado = random.choice(new_alumnos)

    elegido = st.session_state.seleccionado or "ninguno"
    st.markdown(f"""
        <div style='border: 2px solid #4CAF50; border-radius: 10px; padding: 20px; margin-top: 10px; 
                    background-color:#f0f0f0; text-align:center; font-size:20px; color:#000000;'>
            Estudiante elegido: <strong>{elegido}</strong>
        </div>
    """, unsafe_allow_html=True)

    # ---------- Mostrar todos los alumnos en recuadros ----------
    st.markdown("### 👩‍🎓 Lista de alumnos")
    for est in new_alumnos:
        st.markdown(f"""
            <div style='border: 1px solid #888; border-radius: 5px; padding: 10px; margin: 5px; 
                        background-color:#ffffff; color:#000000;'>
                {est}
            </div>
        """, unsafe_allow_html=True)

    # ---------- Guardar asistencia ----------
    def guardar_resultado(valor):
        fecha = datetime.today().strftime("%Y-%m-%d")
        row1 = sheet.row_values(1)
        
        try:
            col_fecha = row1.index(fecha) + 1
        except ValueError:
            col_fecha = len(row1) + 1
            sheet.resize(rows=len(sheet.get_all_values()), cols=col_fecha)
            sheet.update_cell(1, col_fecha, fecha)
        
        alumnos_list = sheet.col_values(1)
        fila = alumnos_list.index(st.session_state.seleccionado) + 1
        sheet.update_cell(fila, col_fecha, valor)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Entregado") and st.session_state.seleccionado:
            guardar_resultado("E")
            st.success("Guardado como ENTREGADO ✅")
    with col2:
        if st.button("❌ No entregado") and st.session_state.seleccionado:
            guardar_resultado("X")
            st.error("Guardado como NO ENTREGADO ❌")
