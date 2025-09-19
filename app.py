import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import random

# ---------- CONFIG ----------
SPREADSHEET_ID = "12BC_5JMZay0ntdmDMUx2eYAQFt-r1d6SoPBIPJOh2EQ"  # tu ID de hoja

# ---------- Autenticación usando Streamlit Secrets ----------
creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1  # abrimos por ID

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
        if username_input == "admin" and password_input == "1234":
            st.session_state.logged_in = True
            st.session_state.username = username_input
            st.success(f"Bienvenido, {username_input}!")
        else:
            st.error("Usuario o contraseña incorrectos ❌")
else:
    st.title(f"👋 Bienvenido, {st.session_state.username}")

    # ---------- Leer alumnos ----------
    alumnos = sheet.col_values(1)[1:]  # saltamos el encabezado
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
    # Recuadro del estudiante elegido
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
        try:
            col_fecha = sheet.row_values(1).index(fecha) + 1
        except ValueError:
            col_fecha = len(sheet.row_values(1)) + 1
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
