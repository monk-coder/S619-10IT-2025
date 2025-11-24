from flask import Flask, request, jsonify, render_template
from database import db
from models import User, ShopItem
from game_service import GameService
import time
import logging
from threading import Thread
import config

app = Flask(__name__,
            template_folder='../frontend',
            static_folder='../frontend',
            static_url_path='')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

game_service = GameService()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/game/<int:user_id>')
def game_page(user_id):
    return render_template('index.html', user_id=user_id)


@app.route('/api/user/<int:user_id>')
def get_user_data(user_id):
    user = db.get_user(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user = db.update_energy(user)
    db.save_user(user)

    return jsonify({
        'user_id': user.user_id,
        'username': user.username,
        'score': user.score,
        'coins': user.coins,
        'energy': user.energy,
        'max_energy': user.max_energy,
        'level': user.level,
        'total_clicks': user.total_clicks,
        'double_click': user.double_click,
        'auto_clicker': user.auto_clicker,
        'fast_recovery': user.fast_recovery,
        'achievements': db.get_achievements(user_id)
    })


@app.route('/api/click/<int:user_id>', methods=['POST'])
def handle_click(user_id):
    user = db.get_user(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    result = game_service.process_click(user)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)


@app.route('/api/shop/<int:user_id>/<item>', methods=['POST'])
def buy_item(user_id, item):
    user = db.get_user(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if item not in ShopItem.ITEMS:
        return jsonify({'error': 'Invalid item'}), 400

    item_data = ShopItem.ITEMS[item]

    if user.coins < item_data['price']:
        return jsonify({'error': 'Not enough coins'}), 400

    for field, value in item_data['effect'].items():
        setattr(user, field, value)

    user.coins -= item_data['price']
    db.save_user(user)

    return jsonify({
        'success': True,
        'new_coins': user.coins,
        'item': item_data['name']
    })


@app.route('/api/leaderboard')
def get_leaderboard():
    leaders = db.get_leaderboard(100)
    return jsonify(leaders)


@app.route('/api/leaderboard/user/<int:user_id>')
def get_user_rank(user_id):
    rank = db.get_user_rank(user_id)
    user = db.get_user(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'rank': rank,
        'username': user.username,
        'score': user.score,
        'level': user.level,
        'total_clicks': user.total_clicks
    })


@app.route('/api/achievements/<int:user_id>')
def get_user_achievements(user_id):
    achievements = db.get_achievements(user_id)
    return jsonify(achievements)


def auto_clicker_worker():
    while True:
        try:
            users = db.get_users_with_auto_clicker()
            current_time = int(time.time())

            for user in users:
                if current_time - user.last_auto_click >= 1:
                    user.score += user.auto_clicker
                    user.coins += user.auto_clicker
                    user.total_clicks += user.auto_clicker
                    user.last_auto_click = current_time
                    db.save_user(user)

            time.sleep(1)
        except Exception as e:
            logger.error(f"Error in auto-clicker: {e}")
            time.sleep(5)


def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    auto_clicker_thread = Thread(target=auto_clicker_worker, daemon=True)
    auto_clicker_thread.start()
    run_flask()