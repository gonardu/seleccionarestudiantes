import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import random

# ---------- CONFIG ----------
SCOPE = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "streamlitasistencia-e6d8319eeb78.json"  # tu JSON descargado
SPREADSHEET_NAME = "seleccion aleatoria - prueba"           # nombre de tu Google Sheet

# ---------- Autenticación ----------
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
client = gspread.authorize(creds)
sheet = client.open(SPREADSHEET_NAME).sheet1

# ---------- SESSION STATE ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "seleccionado" not in st.session_state:
    st.session_state.seleccionado = None

# ---------- LOGIN SIMPLIFICADO ----------
if not st.session_state.logged_in:
    st.title("🔒 Login")
    username_input = st.text_input("Usuario")
    password_input = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        # Aquí ponés tu validación de contraseña
        if username_input == "admin" and password_input == "1234":
            st.session_state.logged_in = True
            st.session_state.username = username_input
            st.success(f"Bienvenido, {username_input}!")
        else:
            st.error("Usuario o contraseña incorrectos ❌")
else:
    st.title(f"👋 Bienvenido, {st.session_state.username}")

    # ---------- Leer alumnos de la hoja ----------
    alumnos = sheet.col_values(1)[1:]  # saltamos el encabezado
    alumnos_text = "\n".join(alumnos)
    new_alumnos = st.text_area("Lista de alumnos (uno por línea)", alumnos_text).splitlines()
    if st.button("Guardar lista"):
        # Borro lista anterior y escribo nueva
        sheet.resize(len(new_alumnos)+1, 1)
        sheet.update("A2:A", [[a] for a in new_alumnos])
        st.success("Lista guardada ✅")

    # ---------- Selección aleatoria ----------
    st.markdown("### 🎯 Selección de alumno")
    if st.button("Seleccionar alumno"):
        if new_alumnos:
            st.session_state.seleccionado = random.choice(new_alumnos)

    elegido = st.session_state.seleccionado or "ninguno"
    st.markdown(f"**Estudiante elegido:** {elegido}")

    # ---------- Guardar asistencia ----------
    def guardar_resultado(valor):
        fecha = datetime.today().strftime("%Y-%m-%d")
        try:
            col_fecha = sheet.row_values(1).index(fecha) + 1
        except ValueError:
            col_fecha = len(sheet.row_values(1)) + 1
            sheet.update_cell(1, col_fecha, fecha)
        # Buscar fila del alumno
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
