from app import create_app
# from app.blueprints.rankings.models import RankingTable

app = create_app()

# @app.shell_context_processor
# def make_context():
#     return {
#         # 'db': db,
#         # 'RankingTable': RankingTable
#     }