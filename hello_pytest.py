# app.py
import requests

def obtener_usuario(user_id):
    response = requests.get(f"https://api.example.com/users/{user_id}")
    f=open("response.out", "w")
    f.write(f"{response.json()}")
    f.close()
    return response.json()

# test_app.py
def test_obtener_usuario(mocker):
    # Simular requests.get
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"id": 1, "name": "Juan"}
    
    mock_get = mocker.patch("requests.get", return_value=mock_response)
    
    # Ejecutar función bajo prueba
    resultado = obtener_usuario(1)
    
    # Verificaciones
    assert resultado["name"] == "Juan"
    mock_get.assert_called_once_with("https://api.example.com/users/1")
