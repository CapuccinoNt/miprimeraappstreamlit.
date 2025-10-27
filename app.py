import streamlit as st

# Título de la app
st.title("Te dire tu edad")

# Texto simple
st.write("Hola, te dire tu edad EXACTA")

# Un input interactivo
nombre = st.text_input("¿Cuantos años tienes?")

# Respuesta condicional
if nombre:
    st.write(f"tienes {nombre} años")

# Un botón
if st.button("Presiona aquí"):
    st.balloons()  # Animación de globos
    st.success("¡Funciona perfectamente!")
