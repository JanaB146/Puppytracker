from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from collections import defaultdict

# Geburtsdatum von Luna
birthdate = datetime(2025, 2, 20)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class WeightEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float(10), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<WeightEntry {self.id} - {self.weight}kg>'

# Datenbank anlegen
with app.app_context():
    db.create_all()

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        try:
            weight_value = float(request.form['weight'])
            date_str = request.form['date']
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, KeyError):
            return "Bitte gib ein gültiges Gewicht (z.B. 74.5) und Datum an."

        new_entry = WeightEntry(weight=weight_value, date_created=date_obj)

        try:
            db.session.add(new_entry)
            db.session.commit()
            return redirect('/')
        except:
            return "Es gab ein Problem beim Speichern des Gewichts."
    else:
        entries = WeightEntry.query.order_by(WeightEntry.date_created).all()

        # Monatliche Gruppierung
        month_weights = defaultdict(list)
        latest_month = 0

        for entry in entries:
            if entry.date_created:
                delta_months = (entry.date_created.year - birthdate.year) * 12 + (entry.date_created.month - birthdate.month)
                if entry.date_created.day < 20:
                    delta_months -= 1
                month_weights[delta_months].append(entry.weight)
                latest_month = max(latest_month, delta_months)

        # Skala geht einen Monat weiter als der letzte mit Daten
        extended_month = latest_month + 1

        labels = [f"Monat {i}" for i in range(extended_month + 1)]

        weights = [0.0]  # Start bei 0
        for i in range(1, extended_month + 1):
            if i in month_weights:
                weights.append(month_weights[i][-1])
            else:
                weights.append(weights[-1])  # Linie durchziehen mit letztem bekannten Wert

        return render_template("index.html", entries=entries, dates=labels, weights=weights)

@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = WeightEntry.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return "Es liegt ein Problem beim Löschen des Eintrags vor.."

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    entry = WeightEntry.query.get_or_404(id)
    if request.method == 'POST':
        try:
            entry.weight = float(request.form['weight'])
            db.session.commit()
            return redirect('/')
        except:
            return "Ohje - ein Problem beim Updating des Eintrags.."
    else:
        return render_template('update.html', entry=entry)

if __name__ == "__main__":
    app.run(debug=True)
