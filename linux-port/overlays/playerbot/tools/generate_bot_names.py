# -*- coding: utf-8 -*-
"""The pool of human nicknames the bots wear, and the SQL that hands them out.

"Pozdrawiam pana botarek7 jest kotem ale brzmi jak bot" - kiciamol, and
jaroszv2 right after: "najgorzej jak biegasz wsrod botow i szukasz tego jednego
nicku a zlewaja sie wszystkie z tymi numerkami". A world of botX7 reads as a
world of bots however well they behave.

The pool has three parts. Two are written by people: 1500 nicknames from
jaksiezabic (10 September, "do lekkiej edycji") and 1000 from Iwakura (11
September, with the patrons' own nicks in it - Tieru agreed to those). The
third is composed, because the cohort is 2500 and about 2240 written names do
not cover it with room to spare - and it is composed from words *taken out of
the written names* in the shapes those names actually have, so a generated
name is not a second dialect. The first version composed everything as
Prefix+Adjective+Noun+Suffix from twenty adjectives and forty nouns, and
Iwakura sent his list with the note that the names should be "bardziej rozne":
2100 names in one grammar are one name.

Two things a name says about a character are respected when they are said
clearly. A name with a class in it - Wlucznia, Szaman, Sura, Woj, Fms, Ninja -
goes to a bot of that class, and a name that is plainly a woman's - Szamanka,
Krolowa, Marysia - goes to a female character; "ninja szamanka ale to sura"
was the Discord's own screenshot. Names that say neither go to anybody. The
pairing is done in SQL in four passes, most specific first.

Nothing about renaming is dangerous, and it is worth writing down why:
CPlayerBotManager::LoadRegisteredBots accepts a character by its account login
(playerbot_NNN), its social id and its player_index row, and never looks at the
name; both panels ask the account too; and generate_seed.py treats a renamed
character as still the character the registry describes as long as
common.playerbot_name_history agrees. So the name is the one part of a bot's
identity nothing depends on.

    python linux-port/overlays/playerbot/tools/generate_bot_names.py
"""
from __future__ import print_function

import collections
import hashlib
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OVERLAY = os.path.abspath(os.path.join(HERE, '..'))
REPO = os.path.abspath(os.path.join(OVERLAY, '..', '..', '..'))
COMMUNITY = [
    os.path.join(OVERLAY, 'data', 'bot_names_community.txt'),
    os.path.join(OVERLAY, 'data', 'bot_names_iwakura.txt'),
]
OUT_SQL = os.path.join(OVERLAY, 'sql', 'playerbot_names.sql')
MIRROR_SQL = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot',
                          'playerbot_names.sql')

# Room for the 2500 seeded bots and for an operator who grows the cohort.
TARGET = 3600
# common/length.h: CHARACTER_NAME_MAX_LEN. player.name is varchar(24), and the
# client draws the name over the head, so shorter is better than exactly 24.
MAX_LEN = 20

# What must never be in the pool: two crude entries.
BLOCKED_STEMS = ('ksujebomoge',)
# A bot must not look like the thing the panels used to identify it by, or the
# rename would be pointless - and it must not look like staff.
BLOCKED_PREFIXES = ('bot', 'gm', 'admin', 'mod', 'system', 'serwer', 'server')

# --- what a name says about its owner ---------------------------------------
# Class words as they occur in the written lists (lower case, matched as a
# substring of the lower-cased name). The engine's job is race % 4:
# 0 warrior, 1 assassin (ninja), 2 sura, 3 shaman.
JOB_WORDS = {
    0: ('wojownik', 'wojowniczk', 'wojek', 'wojka', 'woj', 'rycerz', 'mielony',
        'mielona', 'body', 'mental', 'topor', 'miecz', 'berserk', 'tarcza'),
    1: ('ninja', 'wlucznia', 'dagger', 'sztylet', 'lucznik', 'luczniczk', 'archer',
        'rib', 'strzala', 'lurer', 'kusza', 'luk'),
    2: ('sura', 'fms', 'duch', 'czarodziej', 'czarnoksieznik', 'mag'),
    3: ('szamank', 'szaman', 'healer', 'heal', 'buffka', 'buff', 'lecz'),
}
# Words that only ever describe a woman, or that are women's first names in
# the lists. Everything not here is "either", never "male": a man's name
# forced onto a female character reads as a joke, an unmarked name does not.
FEMALE_WORDS = ('szamanka', 'szamanki', 'wojowniczka', 'luczniczka', 'czarodziejka',
                'krolowa', 'krolewna', 'ksiezniczka', 'buffka', 'ninjaka', 'zona',
                'laska', 'panna', 'pani', 'mama', 'siostra', 'babcia', 'ciocia',
                'kobieta', 'dziewczyna', 'badgirl', 'sexi', 'seksi', 'potargana',
                'zakochana', 'pozytywna', 'nieuczesana', 'spracowana', 'zazdrosna',
                'zniewolona', 'nerwowa', 'slodka', 'truskawkowa', 'malinowa',
                'poziomkowa', 'truskawka', 'malina', 'mizeria', 'marta', 'ewa',
                'ania', 'kasia', 'kasiul', 'marysia', 'paula', 'wiki', 'natalka',
                'urszulka', 'izulka', 'inulka', 'basiucha', 'lalunia', 'niunieczka',
                'maniura', 'wiktoria', 'mariola', 'muszynianka', 'papuszka',
                'arya', 'antalea', 'elendire', 'harlekinchen', 'bliss', 'extasy',
                'strawberry', 'apusiowa', 'illuminata', 'amarena', 'nylzka',
                'mayuri', 'kitsu', 'clairlune', 'dziubasek', 'zafiranki')
MALE_WORDS = ('pan', 'krol', 'lord', 'ojciec', 'brat', 'wujek', 'dziadek', 'syn',
              'ksiaze', 'ksiecio', 'chlop', 'mister', 'sir', 'don', 'kapral',
              'brygadzista', 'strazak', 'ziomek', 'ziomal', 'kolega', 'kumpel',
              'wojtek', 'michal', 'patryk', 'bartek', 'kacper', 'daniel', 'kamil',
              'pawel', 'piotrek', 'seba', 'grzes', 'lukasz', 'andrzej', 'antoni',
              'robert', 'norbi', 'dawid', 'zbyszek', 'remigiusz', 'julian', 'wiesio')


def read_written(path):
    """One list as written, minus what does not belong in it."""
    out = []
    for line in io.open(path, encoding='utf-8'):
        name = line.strip()
        if not name or name.startswith('#'):
            continue
        if acceptable(name):
            out.append(name)
    return out


def acceptable(name):
    # check_name_alphabet in the engine (locale_service.cpp, the english
    # locale's rule) takes letters and digits and nothing else - an underscore
    # is refused at the character screen, so it is refused here too, or a bot
    # would wear a name no player could have. The first character is a letter
    # so a name never reads as a number.
    if not re.match(r'^[A-Za-z][A-Za-z0-9]*$', name):
        return False
    if len(name) < 3 or len(name) > MAX_LEN:
        return False
    low = name.lower()
    if any(stem in low for stem in BLOCKED_STEMS):
        return False
    if any(low.startswith(p) for p in BLOCKED_PREFIXES):
        return False
    return True


def dedupe(names):
    seen = set()
    out = []
    for n in names:
        if n.lower() in seen:
            continue
        seen.add(n.lower())
        out.append(n)
    return out


def tag(name):
    """(job or None, sex or None) from what the name says. sex: 0 male, 1 female."""
    low = name.lower()
    job = None
    for j, words in JOB_WORDS.items():
        if any(w in low for w in words):
            job = j
            break
    sex = None
    if any(w in low for w in FEMALE_WORDS):
        sex = 1
    elif any(re.search(r'(^|[^a-z])' + re.escape(w) + r'([^a-z]|$)', low) or
             low.startswith(w) or low.endswith(w) for w in MALE_WORDS):
        sex = 0
    return job, sex


# --- composing the rest ------------------------------------------------------
def tokens_of(name):
    """CamelCase pieces of a written name, letters only, three letters or more."""
    core = re.sub(r'^(xX|Xx|xXx)|(Xx|xX|xXx)$', '', name)
    parts = re.findall(r'[A-Z]+[a-z]*|[a-z]+', core)
    out = []
    for p in parts:
        # Four letters or more, and never an all-caps run: "SLU", "GMa" and
        # "PL" are tags people hang on a name, not words to build one from -
        # the first draft produced MezaSlu and MaxaGma out of them.
        if len(p) >= 4 and p.isalpha() and not p.isupper():
            out.append(p[0].upper() + p[1:].lower())
    return out


def vocabulary(written):
    counts = collections.Counter()
    for n in written:
        for t in tokens_of(n):
            counts[t] += 1
    # A word that appears in at least three written names is one the
    # community uses; a token seen once or twice is somebody's private joke,
    # a typo, or half of a name that only makes sense whole.
    words = sorted(w for w, c in counts.items() if c >= 3)
    return words


def stable_int(text, mod):
    return int(hashlib.sha256(text.encode('ascii')).hexdigest(), 16) % mod


def compose(written, target):
    """Fill the pool from the written names' own words, in their own shapes.

    Deterministic: every candidate is placed by a hash of itself, so the pool
    is the same on every machine and every run, and a bot renamed today keeps
    that name through every later regeneration.
    """
    seen = set(n.lower() for n in written)
    words = vocabulary(written)
    if len(words) < 40:
        return []
    need = max(0, target - len(written))
    # The shapes written names have, in their measured proportions: two words
    # (most), a word with digits, xX brackets, a lower-case word with digits.
    shapes = ['two'] * 58 + ['digits'] * 24 + ['xx'] * 10 + ['lower'] * 8
    candidates = []
    i = 0
    tries = 0
    while len(candidates) < need and tries < need * 40:
        tries += 1
        seed = 'pool-%d' % i
        i += 1
        a = words[stable_int(seed + 'a', len(words))]
        b = words[stable_int(seed + 'b', len(words))]
        if a == b:
            continue
        shape = shapes[stable_int(seed + 's', len(shapes))]
        if shape == 'two':
            name = a + b
        elif shape == 'digits':
            kind = stable_int(seed + 'k', 3)
            if kind == 0:
                name = a + str(1990 + stable_int(seed + 'y', 21))
            elif kind == 1:
                name = a + str(stable_int(seed + 'n', 90) + 10)
            else:
                name = a + b + str(stable_int(seed + 'n', 90) + 10)
        elif shape == 'xx':
            name = 'xX' + a + b + 'Xx'
        else:
            name = (a + b).lower()
            if stable_int(seed + 'd', 2):
                name += str(stable_int(seed + 'n', 90) + 10)
        if not acceptable(name) or name.lower() in seen:
            continue
        seen.add(name.lower())
        candidates.append(name)
    candidates.sort(key=lambda n: hashlib.sha256(n.encode('ascii')).hexdigest())
    return candidates[:need]


def sql_literal(value):
    return "'" + value.replace('\\', '\\\\').replace("'", "''") + "'"


def sql_or_null(value):
    return 'NULL' if value is None else str(value)


def render(pool):
    rows = []
    for index, name in enumerate(pool, start=1):
        job, sex = tag(name)
        rows.append('(%d,%s,%s,%s)' % (index, sql_literal(name), sql_or_null(job),
                                        sql_or_null(sex)))
    chunks = []
    step = 100
    for start in range(0, len(rows), step):
        chunks.append('INSERT INTO playerbot_name_pool (n, name, job, sex) VALUES\n    ' +
                      ',\n    '.join(rows[start:start + step]) + ';')
    values = '\n'.join(chunks)
    return TEMPLATE.replace('@@COUNT@@', str(len(pool))).replace('@@VALUES@@', values)


# One pass of the pairing: bots not yet planned whose (job, sex) the pass looks
# at, joined by row number within that bucket to the free names tagged for it.
# @@BOT_KEY@@ / @@NAME_KEY@@ are the bucket columns; @@NAME_WHERE@@ selects the
# names this pass may use. A name tagged for a class but not a sex goes to any
# bot of that class in pass 2, a name tagged only female to any woman in pass
# 3, an untagged name to anybody left in pass 4.
PASS = u"""
INSERT INTO playerbot_name_plan (pid, seed_name, human_name)
SELECT waiting.pid, waiting.seed_name, free.name
  FROM (
        SELECT p.id AS pid, p.name AS seed_name,
               MOD(p.job, 4) AS job,
               IF(p.job IN (1, 3, 4, 6), 1, 0) AS sex,
               ROW_NUMBER() OVER (PARTITION BY @@BOT_KEY@@ ORDER BY p.id) AS rn
          FROM player.player AS p
          JOIN account.account AS a ON a.id = p.account_id
         WHERE LEFT(a.login, 10) = 'playerbot_'
           AND p.name LIKE 'bot%'
           AND NOT EXISTS (SELECT 1 FROM common.playerbot_name_history AS h
                            WHERE h.pid = p.id)
           AND NOT EXISTS (SELECT 1 FROM playerbot_name_plan AS pl
                            WHERE pl.pid = p.id)
       ) AS waiting
  JOIN (
        SELECT np.name, np.job, np.sex,
               ROW_NUMBER() OVER (PARTITION BY @@NAME_KEY@@ ORDER BY np.n) AS rn
          FROM playerbot_name_pool AS np
         WHERE @@NAME_WHERE@@
           AND NOT EXISTS (SELECT 1 FROM player.player AS px
                            WHERE px.name = np.name)
           AND NOT EXISTS (SELECT 1 FROM common.playerbot_name_history AS h2
                            WHERE h2.human_name = np.name)
           AND NOT EXISTS (SELECT 1 FROM playerbot_name_plan AS pl2
                            WHERE pl2.human_name = np.name)
       ) AS free
    ON free.rn = waiting.rn @@JOIN@@
 WHERE @playerbot_human_names = '1';
"""

# The bot side partitions by the expressions themselves: job and sex are
# computed from p.job in the same SELECT, and a window function cannot see
# the aliases of the list it belongs to.
BOT_JOB = 'MOD(p.job, 4)'
BOT_SEX = 'IF(p.job IN (1, 3, 4, 6), 1, 0)'
PASSES = [
    # (bot bucket, name bucket, which names, extra join condition)
    (BOT_JOB + ', ' + BOT_SEX, 'np.job, np.sex',
     'np.job IS NOT NULL AND np.sex IS NOT NULL',
     'AND free.job = waiting.job AND free.sex = waiting.sex'),
    (BOT_JOB, 'np.job',
     'np.job IS NOT NULL AND np.sex IS NULL',
     'AND free.job = waiting.job'),
    (BOT_SEX, 'np.sex',
     'np.job IS NULL AND np.sex IS NOT NULL',
     'AND free.sex = waiting.sex'),
    ('1', '1',
     'np.job IS NULL AND np.sex IS NULL',
     ''),
]


def render_passes():
    out = []
    for bot_key, name_key, name_where, join in PASSES:
        p = PASS
        # PARTITION BY needs a column list; the bucket "1" of the last pass
        # is written as a constant partition on purpose.
        p = p.replace('@@BOT_KEY@@', bot_key)
        p = p.replace('@@NAME_KEY@@', name_key)
        p = p.replace('@@NAME_WHERE@@', name_where)
        p = p.replace('@@JOIN@@', join)
        out.append(p)
    return '\n'.join(out)


TEMPLATE = u"""-- Human nicknames for the playerbots. GENERATED - edit
-- linux-port/overlays/playerbot/tools/generate_bot_names.py and re-run it.
--
-- Applied by mariadb/playerbot/apply.sh after the seed, guarded by
-- @playerbot_human_names, which apply.sh sets from M2_PLAYERBOT_HUMAN_NAMES:
--
--   1        rename every bot still called bot<something>   (the default)
--   0        leave every name exactly as it is
--   restore  put the seed names back and forget the renames
--
-- Only a character whose account login is playerbot_NNN is ever touched, and
-- only while it still carries the name the seed gave it - so a bot an operator
-- renamed by hand keeps that name, and no character of a person is reachable
-- from here at all.
--
-- The old name is kept in common.playerbot_name_history, which is what makes
-- 'restore' possible and what stops a second run renaming the same bot twice.

-- A temporary table needs a default database and the client this is fed to has
-- selected none; playerbots_seed.sql opens the same way and for the same
-- reason. Every other table is named in full, so which one it is does not
-- matter beyond that.
USE player;

CREATE TABLE IF NOT EXISTS common.playerbot_name_history (
    pid        INT UNSIGNED NOT NULL,
    seed_name  VARCHAR(24) NOT NULL,
    human_name VARCHAR(24) NOT NULL,
    renamed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (pid),
    KEY human_name (human_name)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

SET @playerbot_human_names = IFNULL(@playerbot_human_names, '1');

-- --------------------------------------------------------------------------
-- restore: the seed name goes back, and only onto a character that still
-- wears the name this table handed it. A bot renamed again by hand afterwards
-- is somebody's deliberate choice and is left alone.
-- --------------------------------------------------------------------------
UPDATE player.player AS p
  JOIN common.playerbot_name_history AS h ON h.pid = p.id
   SET p.name = h.seed_name
 WHERE @playerbot_human_names = 'restore'
   AND BINARY p.name = BINARY h.human_name;

-- Single-table form on purpose: the multi-table DELETE ... FROM x AS a needs a
-- default database, and this file is fed to a client that has selected none.
DELETE FROM common.playerbot_name_history
 WHERE @playerbot_human_names = 'restore';

SELECT CONCAT('playerbot names: restored ', ROW_COUNT(), ' seed name(s)')
       AS playerbot_names_note
  FROM DUAL
 WHERE @playerbot_human_names = 'restore';

-- --------------------------------------------------------------------------
-- The pool: @@COUNT@@ names. Two lists written by people (jaksiezabic's 1500
-- and Iwakura's 1000, less duplicates and what does not belong) and the rest
-- composed from their words. job: 0 warrior, 1 ninja, 2 sura, 3 shaman, NULL
-- any; sex: 0 male, 1 female, NULL either - what the name itself says.
-- --------------------------------------------------------------------------
DROP TEMPORARY TABLE IF EXISTS playerbot_name_pool;
CREATE TEMPORARY TABLE playerbot_name_pool (
    n    INT UNSIGNED NOT NULL PRIMARY KEY,
    name VARCHAR(24) NOT NULL,
    job  TINYINT NULL,
    sex  TINYINT NULL,
    UNIQUE KEY name (name),
    KEY bucket (job, sex, n)
) ENGINE=MEMORY DEFAULT CHARSET=latin1;

@@VALUES@@

-- --------------------------------------------------------------------------
-- Who gets one, and which. Four passes, the most specific first: a name that
-- names a class and a sex goes to a bot of that class and sex, then class
-- only, then sex only, then the rest to whoever is left. Within a pass both
-- sides are numbered by a window function inside their bucket and joined on
-- the number, so the pairing is one statement per pass and stable: the lowest
-- free name goes to the lowest waiting PID of the same bucket. player.job is
-- the race: race % 4 is the class, and 1/3/4/6 are the female models.
--
-- A name is free only when no character in the world wears it - player.name is
-- indexed but not unique, so nothing but this check stops two characters
-- sharing one - and when neither this table nor an earlier pass has handed
-- it out.
-- --------------------------------------------------------------------------
DROP TEMPORARY TABLE IF EXISTS playerbot_name_plan;
CREATE TEMPORARY TABLE playerbot_name_plan (
    pid        INT UNSIGNED NOT NULL PRIMARY KEY,
    seed_name  VARCHAR(24) NOT NULL,
    human_name VARCHAR(24) NOT NULL,
    UNIQUE KEY human_name (human_name)
) ENGINE=MEMORY DEFAULT CHARSET=latin1;
@@PASSES@@
INSERT INTO common.playerbot_name_history (pid, seed_name, human_name)
SELECT pid, seed_name, human_name FROM playerbot_name_plan;

UPDATE player.player AS p
  JOIN playerbot_name_plan AS pl ON pl.pid = p.id
   SET p.name = pl.human_name;

-- HAVING, not WHERE: the aggregate returns one row over an empty plan, and a
-- 'restore' run would otherwise report "gave 0" straight after "restored 2500".
SELECT CONCAT('playerbot names: gave ', COUNT(*), ' bot(s) a human nickname')
       AS playerbot_names_note
  FROM playerbot_name_plan
HAVING @playerbot_human_names = '1';

-- A cohort larger than the pool is the one way this runs out; say so rather
-- than leaving an operator to wonder why some bots kept their seed names.
SELECT CONCAT('playerbot names: WARNING ', COUNT(*),
              ' bot(s) still carry a seed name - the pool of @@COUNT@@ is used up')
       AS playerbot_names_note
  FROM player.player AS p
  JOIN account.account AS a ON a.id = p.account_id
 WHERE @playerbot_human_names = '1'
   AND LEFT(a.login, 10) = 'playerbot_'
   AND p.name LIKE 'bot%'
HAVING COUNT(*) > 0;

DROP TEMPORARY TABLE IF EXISTS playerbot_name_plan;
DROP TEMPORARY TABLE IF EXISTS playerbot_name_pool;
"""


def main():
    written = []
    for path in COMMUNITY:
        written += read_written(path)
    written = dedupe(written)
    pool = written + compose(written, TARGET)
    if len(pool) < TARGET:
        print('uwaga: pula ma tylko %d nickow (cel %d)' % (len(pool), TARGET))
    tagged = collections.Counter()
    for n in pool:
        job, sex = tag(n)
        tagged['klasa' if job is not None else '-'] += 1
        tagged['plec' if sex is not None else '.'] += 1
    text = render(pool).replace('@@PASSES@@', render_passes())
    for path in (OUT_SQL, MIRROR_SQL):
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        io.open(path, 'w', encoding='utf-8', newline='\n').write(text)
    digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
    print('napisano %s (%d nickow: %d napisanych, %d zlozonych; %d z klasa, %d z plcia; sha256 %s)'
          % (OUT_SQL, len(pool), len(written), len(pool) - len(written),
             tagged['klasa'], tagged['plec'], digest[:16]))
    print('kopia:   %s' % MIRROR_SQL)
    return 0


if __name__ == '__main__':
    sys.exit(main())
