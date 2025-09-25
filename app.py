import streamlit as st  
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import random
import json
import hashlib

# ---------- CONFIG ----------
USERS_FILE = "users.json"

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# ---------- SESSION STATE ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "sheet_id" not in st.session_state:
    st.session_state.sheet_id = None
if "seleccionado" not in st.session_state:
    st.session_state.seleccionado = None
if "ya_salieron" not in st.session_state:
    st.session_state.ya_salieron = []  # historial de seleccionados

# ---------- LOGIN ----------
st.title("🔒 Login")
users = load_users()

if not st.session_state.logged_in:
    username_input = st.text_input("Usuario", key="login_user")
    password_input = st.text_input("Contraseña", type="password", key="login_pass")
    if st.button("Ingresar", key="login_button"):
        if username_input in users:
            hashed_input = hashlib.sha256(password_input.encode()).hexdigest()
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

    # ---------- Panel de administración ----------
    if st.session_state.username == "admin":
        st.subheader("⚙️ Panel de administración")

        new_user = st.text_input("Nuevo usuario", key="new_user")
        new_pass = st.text_input("Contraseña del nuevo usuario", type="password", key="new_pass")
        
        if st.button("Crear usuario", key="create_user_button"):
            if new_user and new_pass:
                if new_user in users:
                    st.error("⚠️ El usuario ya existe")
                else:
                    hashed_new_pass = hashlib.sha256(new_pass.encode()).hexdigest()
                    users[new_user] = {"password": hashed_new_pass, "alumnos": []}
                    save_users(users)
                    st.success(f"✅ Usuario '{new_user}' creado correctamente")
            else:
                st.error("⚠️ Debes ingresar usuario y contraseña")

    # ---------- Pegar ID de la hoja ----------
    st.markdown("### 📄 Pegar el ID o link de tu Google Sheet")
    sheet_input = st.text_input("ID o link de la hoja", st.session_state.sheet_id if st.session_state.sheet_id else "", key="sheet_input")
    if sheet_input:
        if "https://docs.google.com/spreadsheets/d/" in sheet_input:
            sheet_id = sheet_input.split("/d/")[1].split("/")[0]
        else:
            sheet_id = sheet_input
        st.session_state.sheet_id = sheet_id

    if st.session_state.sheet_id:
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
        new_alumnos = st.text_area("Lista de alumnos (uno por línea)", alumnos_text, key="alumnos_text").splitlines()
        if st.button("Guardar lista", key="save_list_button"):
            sheet.resize(len(new_alumnos)+1, 1)
            sheet.update("A2:A", [[a] for a in new_alumnos])
            st.success("Lista guardada ✅")

        # ---------- Toggle repetir ----------
        st.subheader("Opciones de selección")
        repetir = st.toggle("Repetir", value=False)

        # ---------- Selección aleatoria ----------
        st.markdown("### 🎯 Selección de alumno")
        if st.button("Seleccionar alumno", key="select_random_button"):
            if new_alumnos:
                if repetir:
                    elegido = random.choice(new_alumnos)
                else:
                    restantes = list(set(new_alumnos) - set(st.session_state.ya_salieron))
                    if not restantes:
                        st.error("🙌 Ya salieron todos los alumnos (sin repetición).")
                        elegido = None
                    else:
                        elegido = random.choice(restantes)
                        st.session_state.ya_salieron.append(elegido)

                st.session_state.seleccionado = elegido

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
            if valor_actual:
                nuevo_valor = f"{valor_actual} {valor}"
            else:
                nuevo_valor = valor

            sheet.update_cell(fila, col_fecha, nuevo_valor)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Entregado", key="btn_entregado") and st.session_state.seleccionado:
                guardar_resultado("E")
                st.success("Guardado como ENTREGADO ✅")
        with col2:
            if st.button("❌ No entregado", key="btn_no_entregado") and st.session_state.seleccionado:
                guardar_resultado("X")
                st.error("Guardado como NO ENTREGADO ❌")
