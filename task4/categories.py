"""Study-specific category definitions and supporting annotation vocabularies.

These wordlists are retrospective research choices, not independently validated
semantic labels. Keep category membership separate from the word-kind aid:
the latter only helps decide whether a string is a complete lexical token.
"""

def _terms(text):
    return set(text.casefold().split())


# Exact, retrospective category dictionaries. These define reproducible lexical
# endpoints; they are not an exhaustive or independently validated semantic oracle.
VEHICLE_TERMS = _terms('''car cars auto autos automobile automobiles van vans truck trucks
pickup pickups vehicle vehicles bike bikes bicycle bicycles motorcycle motorcycles
motorbike motorbikes bus buses boat boats plane planes airplane airplanes aeroplane
aeroplanes aircraft tractor tractors taxi taxis cab cabs wagon wagons jeep jeeps
suv suvs rv rvs caravan caravans camper campers sedan sedans scooter scooters
moped mopeds limousine limousines minivan minivans train trains tram trams
trailer trailers atv atvs cart carts lorry lorries saloon saloons buggy buggies
tank tanks ship ships drone drones jet jets skateboard skateboards hoverboard
hoverboards snowmobile snowmobiles''')
AIRCRAFT_TERMS = _terms('''plane planes aircraft airplane airplanes aeroplane aeroplanes
helicopter helicopters jet jets glider gliders drone drones airliner airliners
biplane biplanes seaplane seaplanes floatplane floatplanes warplane warplanes
monoplane monoplanes gyroplane gyroplanes chopper choppers ultralight ultralights
balloon balloons''')
INSTRUMENT_TERMS = _terms('''piano pianos guitar guitars violin violins viola violas cello
cellos flute flutes harp harps lute lutes organ organs keyboard keyboards drum
drums trumpet trumpets saxophone saxophones sax clarinet clarinets oboe oboes
bassoon bassoons accordion accordions harmonica harmonicas harmonium harmoniums
ukulele ukuleles banjo banjos mandolin mandolins xylophone xylophones trombone
trombones tuba tubas instrument instruments piccolo piccolos tambourine tambourines
marimba marimbas vibraphone vibraphones sitar sitars sarangi sarangis sarod sarods
santoor santoors tabla conga congas djembe djembes bagpipe bagpipes timpani
clavichord clavichords harpsichord harpsichords ocarina ocarinas concertina
concertinas recorder recorders whistle whistles celesta celestas melodica melodicas
synthesizer synthesizers synthesiser synthesisers bugle bugles fiddle fiddles
cornet cornets zither zithers erhu balalaika balalaikas shawm shawms panpipe
panpipes bass horn horns snare snares''')
PLACE_TERMS = _terms('''Westminster London Wales Scotland Paris Bologna Morocco Venice
Rome Britain Singapore Ottawa England Italy Newcastle Toronto Greece Canada
Lisbon Leeds Sweden Spain Barcelona Normandy India Holland Portugal Versailles
Japan Sicily Washington Edinburgh Munich Egypt Athens Oregon Cyprus America
Ghana Surrey Frankfurt Bath Kerala Germany Georgia Hawaii Cincinnati Madagascar
Denmark Somerset France Auckland Trinidad Australia Berlin Maine Nottingham
Cleveland Brussels Madrid Thailand Cologne Kiev Kyiv Kyoto Switzerland Brazil
Boston Bavaria Queensland Lebanon Denver Yorkshire Cairo Hungary Atlanta Ireland
Southampton Siberia Vienna Shanghai Mozambique Kenya Jerusalem Warsaw Austria
Colombia Sydney Pompeii Cork Norway Devon Africa Baghdad Haiti Naples Macedonia
Oman Jamaica Oxford Liverpool Dublin Giza Moscow California Berkeley Copenhagen
Florence Wellington Constantinople China Prague Tokyo Asia Indiana Edmonton
Honolulu Turkey Newfoundland Orlando Nagasaki Netherlands Argentina Budapest
Fiji Panama Crete Delhi Zurich Nuremberg Slovenia Lyons Poland Hyderabad Mexico
Europe Taiwan Brisbane Botswana Winnipeg Amsterdam Benin Vancouver Philadelphia
Florida Dubai Cornwall Corfu Mallorca Goa Tenerife Andorra Lanzarote Lincolnshire
Tuscany Cheshire Worcester Napa Sorrento Texas Inverness Belgrade Nicaragua
Puglia Punjab Tirol Split Madeira Ubud Zagreb Cairns Nashville Brooklyn Palma
Malta Tulum Hanoi Alicante Sydney Bangalore Liverpool Luxor Pennsylvania Phuket
Branson Manchester Varanasi Brighton Vermont Bristol Bolton Bournemouth Perth
Bermuda Porto Chelsea Kansas Aruba Aberdeen Croatia Blackpool Nice Switzerland
Belgium Jerusalem Edinburgh Florence Pasadena Hamburg Bethlehem Bologna Belgium
Switzerland Norway Austria Argentina Haiti Trinidad Queensland Queensland''')
DOOR_ACTION_TERMS = _terms('''open push pull turn knock press twist unlock unlatch unbolt
slide shove tug kick lift rotate grasp close shut slam bolt latch lock''')
CATEGORY_LEXICONS = {
    'parking': VEHICLE_TERMS, 'pilot': AIRCRAFT_TERMS, 'music': INSTRUMENT_TERMS,
    'location': PLACE_TERMS, 'action': DOOR_ACTION_TERMS,
}
CATEGORY_DEFINITIONS = {
    'parking': 'Vehicle-type or generic vehicle nouns; manufacturers and model names excluded.',
    'pilot': 'Aircraft-type or generic aircraft nouns; manufacturers/model names and vague craft excluded. Balloon included as an aircraft type.',
    'music': 'Musical instrument names or the generic instrument category; complete conventional names/abbreviations only. Adjectives, parts and presumed prefix completions excluded.',
    'location': 'Recognized single-token geographic names in an explicit finite list. Context-category endpoint, not semantic similarity to baseline the; incomplete multiword place prefixes excluded.',
    'action': 'Explicit door-interaction verbs, including opening/closing actions. Context-category endpoint, not semantic similarity to feel/walk and not a grammaticality or plausibility score.',
}
BRAND_TERMS = _terms('''Toyota Ford Honda Nissan BMW Mercedes Audi Tesla Chevy Chevrolet
Dodge Subaru Volvo Renault Yamaha Polaris Fiat Alfa Buick Cadillac Lexus Mazda
Volkswagen Porsche Peugeot Citroen Hyundai Kia Bentley Ferrari Lamborghini
Ram Prius Civic Jeep Cessna Boeing Piper Airbus Beech Fokker Dornier Douglas
Lockheed Learjet Embraer''')
AMBIGUOUS_TERMS = {
    'parking': _terms('motor hybrid golf semi rover land brand rental diesel civic ram geo hot ml'),
    'pilot': _terms('craft flight air liner fleet shuttle spacecraft rocket carrier transport aircrafts lear apache hurricane phantom concord hercules beaver cub falcon'),
    'music': _terms('strings string keys key brass wind pipe bow viol cell accord ban harmon sar ob t gu c ch f d mand clar xyl hurd har ly uk pian ped sh fl saxes'),
    'location': _terms('new san los las la le el st port lake mount mont monte loch county north south east west northern central upper disney costa hong chiang man al koh pant horseshoe big taur ur eden nice bath paradise'),
    'action': set(),
}
FRAGMENT_TERMS = _terms('monoch melod')

# Common inflections/contemporary words absent from the system dictionary.
EXTRA_COMPLETE_WORDS = _terms('''parents cars vehicles trucks pickups bikes bicycles motorcycles
boats vans planes airplanes helicopters instruments keyboards cellos guitars drums
keys strings hotels assets specs kids brands husbands parked latest own myself
the a an this their our your my his her it its one two three four five six seven
eight nine ten first second third fourth fifth other another all some any new old
same small large big little last next entire whole beautiful sunny different slowly
gently carefully hurriedly newly fully electric electronic acoustic grand wooden
musical sacred classical theme tune stage crowd end body air table wall floor
space phone dishwasher service cable mother husband life scoot camper rv suv atv
open pull push press turn knock look move use cry feel walk speak say think sing
talk read laugh whisper pace stir run wonder realize realise take scream close make
notice put smile sweat get recite play grow sound work write breathe change listen
shout explore shake swing worry count enter panic stumble draw rub crawl drag descend
ring surprise roll fill fold stare understand adjust load weave return try shrink
show remove uncover collect unravel sweep hum remember discuss bark lean scratch
build jump hesitate pray study wipe outline examine lift peel inhale guide empty
follow fear find scan let answer bear lower greet go carry light sense wear stand
converse knit warm grasp pour so sigh wave how strangle collapse smell smash cross
milk shed tie beat tap practice wrap cut give explain stroke stretch pinch pound
fight struggle set sew shovel hear act gently drive count kiss approach experience
slip slide wait chew murmur curse rotate leave comb learn force bite wake hang
trade holding playing watched playing playing''')
