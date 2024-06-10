from flask import Flask, render_template, redirect, url_for, request, session
from flask_session import Session
from bingo import *
import uuid

app = Flask(__name__)

# Configure server-side sessions
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "supersecretkeydonttellanyone"  # You should use a more secure key in production
Session(app)

# Initialize game state
def init_game():
    return {
        'computer_b': create_board(),
        'player_b': create_board(),

        'computer_n': None,
        'player_n': None,

        'player_numbers': [],  # Track player numbers
        'available_numbers': set(range(1, 26)),  # Track computer numbers
        
        'count_p': 0,
        'count_c': 0,

        'winner': None,

        'show_computer': None
    }

@app.route("/", methods=["GET", "POST"])
def first():
    session['game_id'] = str(uuid.uuid4())  # Create a unique session ID for each new visitor
    session[session['game_id']] = init_game()  # Initialize game state for the new session
    return render_template("home.html")

@app.route("/play", methods=["POST", "GET"])
def play():
    game_state = session.get(session['game_id'])

    if request.method == "POST":
        game_state["show_computer"] = True if request.form.get("computer-play") == "on" else None

    if game_state["winner"] is not None:
        return redirect(url_for('won'))
    return render_template(
        "play.html",
        player_b=game_state['player_b'],
        computer_b=game_state['computer_b'] if game_state["show_computer"] else None,
        count_c=game_state["count_c"],
        count_p=game_state["count_p"],
        player_n=game_state["player_n"],
        computer_n=game_state["computer_n"]
    )

@app.route("/mark/<int:player_n>")
def mark(player_n):
    game_state = session.get(session['game_id'])

    if game_state["winner"] is not None:
        return redirect(url_for('won'))

    if player_n not in game_state['player_numbers']:
        find_key_mark(game_state['player_b'], game_state['computer_b'], player_n)

        game_state["player_n"] = player_n
        game_state['player_numbers'].append(player_n)
        
        game_state["count_p"] = check_bingo(game_state['player_b'])
        game_state["count_c"] = check_bingo(game_state['computer_b'])

        if game_state["count_p"] >= 5:
            game_state["winner"] = 1
            session[session['game_id']] = game_state
            return redirect(url_for("won"))

        if game_state["count_c"] >= 5:
            game_state["winner"] = 0
            session[session['game_id']] = game_state
            return redirect(url_for("won"))

        computer_n = ask_computer(game_state['computer_b'])
        game_state['available_numbers'].remove(computer_n)
        game_state["computer_n"] = computer_n

        find_key_mark(game_state['computer_b'], game_state['player_b'], computer_n)

        game_state["count_c"] = check_bingo(game_state['computer_b'])
        game_state["count_p"] = check_bingo(game_state['player_b'])

        if game_state["count_c"] >= 5:
            game_state["winner"] = 0
            session[session['game_id']] = game_state
            return redirect(url_for("won"))

        if game_state["count_p"] >= 5:
            game_state["winner"] = 1
            session[session['game_id']] = game_state
            return redirect(url_for("won"))

    session[session['game_id']] = game_state
    return redirect(url_for('play'))

@app.route("/won", methods=["POST", "GET"])
def won():
    game_state = session.get(session['game_id'])
    if game_state["winner"] == 1:
        winner = "Player"
    elif game_state["winner"] == 0:
        winner = "Computer"
    else:
        return redirect(url_for('play'))

    return render_template(
        "won.html",
        candidate=winner,
        player_b=game_state['player_b'],
        computer_b=game_state['computer_b'],
        count_c=game_state["count_c"],
        count_p=game_state["count_p"],
    )

@app.route("/play-again", methods=["GET", "POST"])
def play_again():
    session[session['game_id']] = init_game()  # Reset the game state for the current session
    if request.method == "POST":
        game_state = session.get(session['game_id'])
        game_state["show_computer"] = True if request.form.get("computer-play") == "on" else None
        session[session['game_id']] = game_state

    return redirect(url_for('play'))

@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    response.cache_control.no_cache = True
    response.cache_control.must_revalidate = True
    response.cache_control.max_age = 0
    return response

if __name__ == "__main__":
    app.run()
