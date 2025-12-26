# test_url_format.py
import requests

# Simular la URL que enviará tu jefe
url = "http://localhost:8000/"

params = {
    'client_name': 'Juan Perez',
    'company_name': 'Grupo Familia',
    'invoice_name': 'FE154',
    'invoice_amount': '150000',
    'invoice_id': '1545',
    'company_domain': 'somosbdc.oficinapro.co',
    'client_phone': '573136632408'  # ⬅️ IMPORTANTE: Agregar el teléfono
}

print("🚀 Enviando por URL GET (formato del jefe)...\n")

try:
    response = requests.get(url, params=params)
    
    print(f"📊 Status Code: {response.status_code}\n")
    print(f"📄 Respuesta:")
    import json
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    print(f"\n🔗 URL generada: {response.url}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ ¡Mensaje enviado!")
        print(f"📱 Link generado: {data['datos']['link']}")
        print(f"   Esperado: https://somosbdc.oficinapro.co/invoice/1545")
    else:
        print("\n❌ Hubo un error")
    
except Exception as e:
    print(f"❌ Error: {e}")
