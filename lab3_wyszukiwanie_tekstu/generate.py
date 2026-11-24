"""Write reproducible English field notes, streamed to CSV."""

import argparse
import csv
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIELDS = ('id', 'title', 'body', 'category', 'region', 'year')
SIZES = (50_000, 250_000, 500_000)
SEED = 732_391
TOPICS = {
    'water': ('riverbank', 'stream crossing', 'drainage basin', 'gravel bar', 'overflow channel'),
    'woodland': ('woodland path', 'forest edge', 'birch stand', 'oak clearing', 'shaded ravine'),
    'coast': ('tidal creek', 'coastal trail', 'shingle beach', 'sand dune', 'salt meadow'),
    'grassland': ('meadow', 'pasture', 'field margin', 'open slope', 'lowland prairie'),
    'urban': ('city park', 'school garden', 'disused rail yard', 'community orchard', 'green roof'),
    'upland': ('hillside trail', 'stone ridge', 'upland pool', 'rocky slope', 'mountain pass'),
}
REGIONS = ('north', 'south', 'east', 'west', 'central')
PLACES = ('Alder Reach', 'Birch Hollow', 'Cedar Vale', 'Driftwood Bay', 'Elm Ridge',
          'Fern Crossing', 'Granite Point', 'Hazel Brook', 'Ivy Bend', 'Juniper Hill',
          'Larch Gap', 'Maple Basin', 'Orchard Rise', 'Pine Knoll', 'Reed Valley', 'Willow Bank')
WEATHER = ('a week of light rain', 'an unusually dry spell', 'a cold morning', 'a warm afternoon',
           'several windy days', 'the first autumn frost', 'an overnight storm', 'a stretch of mild weather')
OPEN = (
    'The field team visited the {site} near {place} after {weather}.',
    'Volunteers met at {place} to check the {site} following {weather}.',
    'A walk through the {site} at {place} followed {weather}.',
    'The survey began near {place}, where a small crew inspected the {site} after {weather}.',
    'Staff returned to the {site} at {place} after {weather} to review the previous season’s notes.',
)
OBSERVATIONS = (
    'They measured {area} square metres of exposed ground and counted {count} clusters of new shoots near the marker posts.',
    'The notebook lists {count} marked sampling points across {area} square metres. Several points were checked twice because the boundaries were difficult to read.',
    'The crew compared {count} samples from a plot of {area} square metres with observations from the previous visit.',
    'Within a survey area of {area} square metres, they marked {count} places for a closer look during the next visit.',
    'A second group recorded {count} changes along the edge of a {area}-square-metre plot and sketched the points on a paper map.',
)
RESTORATION = (
    ('Restoring the site', 'Local crews are restoring the lower slope and have agreed to return in late spring.'),
    ('Restoration field notes', 'The restoration work brought volunteers back to the old footpath.'),
    ('A restored section', 'Crews restored the upper bank last winter and will compare it with the untreated section.'),
    ('A plan to restore access', 'The group hopes to restore access before the next planting season.'),
    ('Maintenance visit', 'A contractor will restore the signs while the team checks the boundary.'),
)
PHRASES = (
    'The crew installed a solar panel beside the instrument shelter and rewired the old gauge.',
    'One solar panel still supplies enough power for the logger on clear afternoons.',
    'A solar panel feeds the new pump, although the battery must be checked after cloudy days.',
    'Two solar panels now charge the backup battery during daylight and power the recorder overnight.',
    'Staff moved the solar panel away from the fence to avoid shade from the hedgerow.',
)
HABITAT = (
    'The shallow wetland provides habitat for frogs and small birds when the pools remain connected.',
    'Farther down the path, the marsh offers sheltered habitat for insects that emerge in spring.',
    'The wetland habitat changes with the water level and is easier to map from the western path.',
    'Several birds use the marsh as feeding habitat during their spring migration.',
    'A narrow wetland corridor links the lower habitat with the shaded ponds nearer the road.',
)
DETAILS = (
    'The crew photographed the same fixed markers so that later visitors can distinguish seasonal changes from shifts in the survey boundary.',
    'Water levels stayed close to the long-term average, but the surface had become softer near the lower gate and some readings were repeated.',
    'Work was delayed while the group found a dry place to spread out the maps and checked the route with staff from the visitor centre.',
    'The written record separates direct observations from suggestions, since several of the proposed changes will need a separate review.',
    'A narrow strip of ground was left alone. The group expects spring growth to make it easier to identify the plants along that strip.',
    'The group compared handwritten notes before leaving and marked the places where two observers had used different names for the same feature.',
    'The crew noted a patch of lichen on a shaded rock and left it in place for a later photographic survey.',
    'An old support post needed attention. Staff described its position in the notebook and marked a safe way around it for later visitors.',
    'The site map now shows where the previous crew ended its survey, which should help the next group repeat the same route.',
)
CLOSE = (
    'A follow-up visit will check whether the changes persist through the next wet season.',
    'The team filed its observations with the local office and requested a brief return visit.',
    'The crew will repeat the measurements once the ground has dried and the new markers are in place.',
    'For the next visit, the team plans to carry a spare field notebook and an extra length of measuring tape.',
    'The field log will be compared with the spring survey before the route is opened to visitors again.',
)


def record(rng, identifier):
    category = rng.choice(tuple(TOPICS))
    site = rng.choice(TOPICS[category])
    place = rng.choice(PLACES)
    year = rng.randint(1995, 2024)
    region = rng.choice(REGIONS)
    title = f'{site.capitalize()} survey at {place}'
    body = [rng.choice(OPEN).format(site=site, place=place, weather=rng.choice(WEATHER)),
            rng.choice(OBSERVATIONS).format(area=rng.randint(35, 2400), count=rng.randint(4, 85))]
    if rng.random() < 0.15:
        heading, sentence = rng.choice(RESTORATION)
        body.append(sentence)
        if rng.random() < 0.37:
            title = f'{heading} at {place}'
        if rng.random() < 0.08:
            body.append('Restoring the adjoining area may help the team compare the two approaches.')
    if rng.random() < 0.065:
        body.append(rng.choice(PHRASES))
        if rng.random() < 0.31:
            title = f'Solar panel inspection at {place}'
    elif rng.random() < 0.065:
        body.append('The log describes the solar installation. The replacement panel will arrive next month.')
    if rng.random() < (0.34 if category in ('water', 'coast') else 0.04):
        body.append(rng.choice(HABITAT))
        if rng.random() < 0.20:
            title = f'Wetland habitat survey at {place}'
        if rng.random() < 0.24:
            body.append('Invasive plants were recorded near the gate and photographed for the maintenance team.')
    body.extend(rng.sample(DETAILS, k=rng.randint(1, 3)))
    body.append(rng.choice(CLOSE))
    return dict(zip(FIELDS, (identifier, title, ' '.join(body), category, region, year)))


def generate(root, seed):
    data = root / 'data'
    results = root / 'results'
    data.mkdir(exist_ok=True)
    results.mkdir(exist_ok=True)
    rng = random.Random(seed)
    target = data / 'field_notes.csv'
    categories, regions = Counter(), Counter()
    hashes = set()
    lengths = 0
    shortest, longest = float('inf'), 0
    with target.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        for identifier in range(1, SIZES[-1] + 1):
            row = record(rng, identifier)
            writer.writerow(row)
            categories[row['category']] += 1
            regions[row['region']] += 1
            body = row['body']
            hashes.add(hashlib.blake2b(body.encode(), digest_size=16).digest())
            lengths += len(body)
            shortest = min(shortest, len(body))
            longest = max(longest, len(body))
            if identifier == 1:
                example = row
            if identifier in SIZES:
                print(f'Wygenerowano {identifier:,} rekordów', flush=True)
    with target.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    profile = {'source': 'generate.py', 'license': 'CC0-1.0', 'seed': seed, 'records': SIZES[-1],
               'bytes': target.stat().st_size, 'sha256': digest, 'body_chars_mean': lengths / SIZES[-1],
               'body_chars_min': shortest, 'body_chars_max': longest,
               'duplicate_bodies': SIZES[-1] - len(hashes), 'categories': dict(categories),
               'regions': dict(regions), 'year_min': 1995, 'year_max': 2024, 'example': example}
    (results / 'dataset.json').write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=SEED)
    generate(ROOT, parser.parse_args().seed)
