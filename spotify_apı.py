from flask import Flask, redirect, request, session, jsonify, render_template
import requests
import base64
from flask import jsonify

# Flask uygulamasını başlat
app = Flask(__name__)
app.secret_key = 'your_secret_key'  

# Spotify API kimlik bilgileri
client_id = 'KENDİ ID'#bunu spotify apı alma bölümünden almak gerekiyor
client_secret = ''
redirect_uri = 'http://localhost:8080/spotify_callback'  # Spotify'daki yönlendirme URI ile aynı olmalısı gerekiyor

# Spotify yetkilendirme URL'si
auth_url = "https://accounts.spotify.com/authorize"
token_url = "https://accounts.spotify.com/api/token"
user_profile_url = "https://api.spotify.com/v1/me"
recommendations_url = "https://api.spotify.com/v1/recommendations"


def get_spotify_auth_url():
    scope = "user-read-private user-read-email user-top-read"  # İzinler (scope)
    auth_params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": scope
    }
    auth_request_url = f"{auth_url}?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope={scope}"
    return auth_request_url


def get_access_token(auth_code):
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode('ascii')
    
    token_data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': redirect_uri
    }

    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(token_url, data=token_data, headers=headers)
    return response.json()


def get_user_profile(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(user_profile_url, headers=headers)
    return response.json()


def get_recommendations(access_token, genre):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'seed_genres': genre,  # Kullanıcının seçtiği müzik türü
        'limit': 5  # Kaç öneri almak istediğimizi belirtiyoruz
    }
    response = requests.get(recommendations_url, headers=headers, params=params)

    print(f"GET {recommendations_url} - Status Code: {response.status_code}")  # Durum kodunu yazdır
    if response.status_code != 200:
        print("Hata:", response.json())  # Hata detayını yazdır
        return None

    return response.json()


@app.route('/')
def index():
    auth_request_url = get_spotify_auth_url()  # Yetkilendirme URL'sini al
    return redirect(auth_request_url)  # Kullanıcıyı bu URL'ye yönlendir


@app.route('/spotify_callback')
def spotify_callback():
    auth_code = request.args.get('code')

    token_response = get_access_token(auth_code)

    if 'access_token' in token_response:
        access_token = token_response['access_token']
        user_profile = get_user_profile(access_token)

        session['access_token'] = access_token  # Erişim token'ını oturumda sakla
        return render_template('user_profile.html', user=user_profile)
    else:
        return "Error in getting access token", 400


@app.route('/recommendations')
def recommendations():
    genre = request.args.get('genre')  
    access_token = session.get('access_token')  

    if not access_token:
        return jsonify({"error": "Erişim token'ı bulunamadı. Lütfen önce giriş yapın."}), 403

    recommendations_data = get_recommendations(access_token, genre)  
    print(recommendations_data)  # API'den gelen yanıtı yazdır

    if not recommendations_data or 'tracks' not in recommendations_data:
        print("API yanıtı beklenildiği gibi değil:", recommendations_data)
        return jsonify({"error": "Öneriler alınamadı."}), 500

    tracks = [
        {
            'album': track['album']['name'],
            'artist': track['artists'][0]['name'],
            'name': track['name'],
            'url': track['external_urls']['spotify']
        }
        for track in recommendations_data.get('tracks', [])
    ]

    return jsonify(tracks)  # JSON yanıtı döndür

if __name__ == '__main__':
    app.run(debug=True, port=8080)
