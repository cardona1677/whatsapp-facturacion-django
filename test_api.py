import requests
import json

url = "http://localhost:8000/api/whatsapp/enviar/"

# ⚠️ Ahora incluye el valor_factura
datos = {
    "numero_factura": "FAC-TEST-001",
    "telefono": "+573136632408",  # Tu número
    "nombre_cliente": "Andrés Poveda",
    "nombre_comercio": "Oficinapro",
    "valor_factura": "$550.000"  # ⬅️ NUEVO: El monto de la factura
}

print("🚀 Enviando mensaje REAL por WhatsApp con plantilla aprobada...\n")

try:
    response = requests.post(url, json=datos)
    
    print(f"📊 Status Code: {response.status_code}\n")
    print(f"📄 Respuesta:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    if response.status_code == 200:
        print("\n✅ ¡REVISA TU WHATSAPP! 📱")
        print("Deberías recibir un mensaje como:")
        print(f"'Hola {datos['nombre_cliente']}, te informamos que tu factura {datos['numero_factura']} por un valor de {datos['valor_factura']} ya fue generada...'")
    else:
        print("\n❌ Hubo un error. Revisa la respuesta arriba.")
    
except Exception as e:
    print(f"❌ Error de conexión: {e}")