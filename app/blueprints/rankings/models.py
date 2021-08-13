# from app import db

# class RankingTable(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     rank = db.Column(db.Integer)
#     country = db.Column(db.Text)
#     player_name = db.Column(db.Text)
#     rank_change = db.Column(db.Text)
#     win_loss = db.Column(db.Text)
#     prize_money = db.Column(db.Text)
#     points_per_tournament = db.Column(db.Text)
#     member_id = db.Column(db.Text, unique=True)

#     date = '';
#     category = '';

#     def __repr__(self) -> str:
#         return f'<Ranking Table for {self.category} on {self.date}>'
    
#     def save(self):
#         db.session.add(self)
#         db.session.commit()
