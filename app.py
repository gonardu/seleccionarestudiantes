import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import random
import json
import hashlib
import os

# ---------- CONFIG ----------
USERS_FILE = "users.json"

# ---------- FUNCIONES ----------
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------- SESSION STATE ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "sheet_id" not in st.session_state:
    st.session_state.sheet_id = None
if "seleccionado" not in st.session_state:
    st.session_state.seleccionado = None

# ---------- LOGIN ----------
st.title("🔒 Login")
users = load_users()

if not st.session_state.logged_in:
    username_input = st.text_input("Usuario")
    password_input = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if username_input in users:
            hashed_input = hash_password(password_input)
            if hashed_input == users[username_input]["password"]:
                st.session_state.logged_in = True
                st.session_state.username = username_input
                st.success(f"Bienvenido, {username_input}!")
            else:
                st.error("Usuario o contraseña incorrectos ❌")
        else:
            st.error("Usuario o contraseña incorrectos ❌")

# ---------- SESIÓN INICIADA ----------
if st.session_state.logged_in:
    st.title(f"👋 Bienvenido, {st.session_state.username}")

    # ---------- PANEL ADMIN ----------
    if st.session_state.username == "admin":
        st.subheader("⚙️ Panel de administración")
        new_user = st.text_input("Nuevo usuario")
        new_pass = st.text_input("Contraseña", type="password")
        if st.button("Crear usuario"):
            if new_user and new_pass:
                users = load_users()
                if new_user in users:
                    st.error("Ese usuario ya existe ❌")
                else:
                    users[new_user] = {"password": hash_password(new_pass)}
                    save_users(users)
                    st.success(f"Usuario '{new_user}' creado ✅")
            else:
                st.error("Completa todos los campos ❌")

    # ---------- Pegar ID de la hoja ----------
    st.markdown("### 📄 Pegar el ID o link de tu Google Sheet")
    sheet_input = st.text_input("ID o link de la hoja", st.session_state.sheet_id if st.session_state.sheet_id else "")
    if sheet_input:
        if "https://docs.google.com/spreadsheets/d/" in sheet_input:
            sheet_id = sheet_input.split("/d/")[1].split("/")[0]
        else:
            sheet_id = sheet_input
        st.session_state.sheet_id = sheet_id

    if st.session_state.sheet_id:
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
        alumnos = sheet.col_values(1)[1:]
        alumnos_text = "\n".join(alumnos)
        new_alumnos = st.text_area("Lista de alumnos (uno por línea)", alumnos_text).splitlines()
        if st.button("Guardar lista"):
            sheet.resize(len(new_alumnos)+1, 1)
            sheet.update("A2:A", [[a] for a in new_alumnos])
            st.success("Lista guardada ✅")

        # ---------- Selección aleatoria ----------
        st.markdown("### 🎯 Selección de alumno")
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

        # ---------- Mostrar todos los alumnos ----------
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
            valor_actual = sheet.cell(fila, col_fecha).value
            nuevo_valor = f"{valor_actual} {valor}" if valor_actual else valor
            sheet.update_cell(fila, col_fecha, nuevo_valor)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Entregado") and st.session_state.seleccionado:
                guardar_resultado("E")
                st.success("Guardado como ENTREGADO ✅")
        with col2:
            if st.button("❌ No entregado") and st.session_state.seleccionado:
                guardar_resultado("X")
                st.error("Guardado como NO ENTREGADO ❌")
