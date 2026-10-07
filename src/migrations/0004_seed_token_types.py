from yoyo import step

__depends__ = {"0003_create_roads"}

# Distribution weights aim for a classic 30-token board:
# 1x Star (Bitcoin)
# 4x High Reward (Level 2)
# 8x Low Reward (Level 1)
# 5x Bandits (Hazards)
# 12x Horseshoes (Neutral)

steps = [
    step(
        """
        INSERT INTO token_types (name, category, money_delta, weight, texture_key) 
        VALUES
            ('Afrikan Tähti', 'reward',  5000,  1, 'merkki-bitcoin-lvl3'),
            ('Level 2 Reward', 'reward',   500,  4, 'merkki-200-iq-lv2'),
            ('Level 1 Reward', 'reward',   300,  8, 'merkki-varoitus-lv1'),
            ('Bandit',         'hazard',     0,  5, 'merkki-special-bandit'),
            ('Horseshoe',      'neutral',    0, 12, 'merkki-special-horseshoe');
        """,
        """
        DELETE FROM token_types 
        WHERE texture_key IN (
            'merkki-bitcoin-lvl3',
            'merkki-200-iq-lv2',
            'merkki-varoitus-lv1',
            'merkki-special-bandit',
            'merkki-special-horseshoe'
        );
        """
    )
]
