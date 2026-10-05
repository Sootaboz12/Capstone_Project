export interface TeamStats {
  wins: number
  losses: number
  ties: number
  pointsFor: number
  pointsAgainst: number
  streak: string
  powerRank: number
  offenseRating: number // 0-100, placeholder composite
  defenseRating: number // 0-100, placeholder composite
  turnoverMargin: number
  homeRecord: string
  awayRecord: string
}

export interface Team {
  id: string
  abbr: string
  city: string
  name: string
  stadium: string
  blurb: string
  conference: 'AFC' | 'NFC'
  division: 'East' | 'North' | 'South' | 'West'
  colors: { primary: string; secondary: string }
  stats: TeamStats
}

// NOTE: stats below are placeholder/mock values for framework purposes only.
// Swap `stats` for a live feed once the prediction backend is wired up.
function mockStats(seed: number): TeamStats {
  const wins = 4 + (seed % 10)
  const losses = 16 - wins
  return {
    wins,
    losses,
    ties: 0,
    pointsFor: 280 + ((seed * 17) % 160),
    pointsAgainst: 260 + ((seed * 11) % 170),
    streak: seed % 2 === 0 ? `W${1 + (seed % 4)}` : `L${1 + (seed % 3)}`,
    powerRank: 1 + (seed % 32),
    offenseRating: 45 + ((seed * 7) % 50),
    defenseRating: 45 + ((seed * 13) % 50),
    turnoverMargin: (seed % 13) - 6,
    homeRecord: `${3 + (seed % 5)}-${5 - (seed % 5)}`,
    awayRecord: `${2 + (seed % 5)}-${6 - (seed % 5)}`,
  }
}

export const teams: Team[] = [
  { id: 'buf', abbr: 'BUF', city: 'Buffalo', name: 'Bills', stadium: 'Highmark Stadium', blurb: "Blue-collar AFC East mainstay, fueled by brutal winters and the rowdy 'Bills Mafia'.", conference: 'AFC', division: 'East', colors: { primary: '#00338D', secondary: '#C60C30' }, stats: mockStats(1) },
  { id: 'mia', abbr: 'MIA', city: 'Miami', name: 'Dolphins', stadium: 'Hard Rock Stadium', blurb: "The NFL's only unbeaten Super Bowl champion, still chasing that perfect record's echo.", conference: 'AFC', division: 'East', colors: { primary: '#008E97', secondary: '#F58220' }, stats: mockStats(2) },
  { id: 'ne', abbr: 'NE', city: 'New England', name: 'Patriots', stadium: 'Gillette Stadium', blurb: 'Six-time Super Bowl champions who turned discipline into a two-decade dynasty.', conference: 'AFC', division: 'East', colors: { primary: '#002244', secondary: '#C60C30' }, stats: mockStats(3) },
  { id: 'nyj', abbr: 'NYJ', city: 'New York', name: 'Jets', stadium: 'MetLife Stadium', blurb: "New York's other football team, forever chasing Broadway Joe's lone title shine.", conference: 'AFC', division: 'East', colors: { primary: '#125740', secondary: '#000000' }, stats: mockStats(4) },
  { id: 'bal', abbr: 'BAL', city: 'Baltimore', name: 'Ravens', stadium: 'M&T Bank Stadium', blurb: "Ground-and-pound defense named for Baltimore's favorite literary bird.", conference: 'AFC', division: 'North', colors: { primary: '#241773', secondary: '#9E7C0C' }, stats: mockStats(5) },
  { id: 'cin', abbr: 'CIN', city: 'Cincinnati', name: 'Bengals', stadium: 'Paycor Stadium', blurb: "Ohio's tiger-striped attack, known for explosive offense and narrow near-misses.", conference: 'AFC', division: 'North', colors: { primary: '#FB4F14', secondary: '#000000' }, stats: mockStats(6) },
  { id: 'cle', abbr: 'CLE', city: 'Cleveland', name: 'Browns', stadium: 'Huntington Bank Field', blurb: 'One of the league\'s original franchises, carried by a fan base that never wavers.', conference: 'AFC', division: 'North', colors: { primary: '#311D00', secondary: '#FF3C00' }, stats: mockStats(7) },
  { id: 'pit', abbr: 'PIT', city: 'Pittsburgh', name: 'Steelers', stadium: 'Acrisure Stadium', blurb: 'Steel Curtain defense and blue-collar grit have defined this franchise for decades.', conference: 'AFC', division: 'North', colors: { primary: '#FFB612', secondary: '#101820' }, stats: mockStats(8) },
  { id: 'hou', abbr: 'HOU', city: 'Houston', name: 'Texans', stadium: 'NRG Stadium', blurb: "Houston's newest major franchise, built around speed on both sides of the ball.", conference: 'AFC', division: 'South', colors: { primary: '#03202F', secondary: '#A71930' }, stats: mockStats(9) },
  { id: 'ind', abbr: 'IND', city: 'Indianapolis', name: 'Colts', stadium: 'Lucas Oil Stadium', blurb: "A passing pedigree that runs from Baltimore's Unitas to Indy's Manning era.", conference: 'AFC', division: 'South', colors: { primary: '#002C5F', secondary: '#A2AAAD' }, stats: mockStats(10) },
  { id: 'jax', abbr: 'JAX', city: 'Jacksonville', name: 'Jaguars', stadium: 'EverBank Stadium', blurb: "Florida's teal-and-gold upstarts, still chasing a first trip to the Super Bowl.", conference: 'AFC', division: 'South', colors: { primary: '#101820', secondary: '#D7A22A' }, stats: mockStats(11) },
  { id: 'ten', abbr: 'TEN', city: 'Tennessee', name: 'Titans', stadium: 'Nissan Stadium', blurb: "A tough-nosed franchise forged from the old Houston Oilers' run-first identity.", conference: 'AFC', division: 'South', colors: { primary: '#0C2340', secondary: '#4B92DB' }, stats: mockStats(12) },
  { id: 'den', abbr: 'DEN', city: 'Denver', name: 'Broncos', stadium: 'Empower Field at Mile High', blurb: 'Mile-high altitude and orange-crush defense have powered decades of AFC West battles.', conference: 'AFC', division: 'West', colors: { primary: '#FB4F14', secondary: '#002244' }, stats: mockStats(13) },
  { id: 'kc', abbr: 'KC', city: 'Kansas City', name: 'Chiefs', stadium: 'GEHA Field at Arrowhead Stadium', blurb: "Kansas City's modern dynasty, pairing a deafening home crowd with relentless offense.", conference: 'AFC', division: 'West', colors: { primary: '#E31837', secondary: '#FFB81C' }, stats: mockStats(14) },
  { id: 'lv', abbr: 'LV', city: 'Las Vegas', name: 'Raiders', stadium: 'Allegiant Stadium', blurb: 'Silver and Black outlaws now calling the Las Vegas Strip home.', conference: 'AFC', division: 'West', colors: { primary: '#000000', secondary: '#A5ACAF' }, stats: mockStats(15) },
  { id: 'lac', abbr: 'LAC', city: 'Los Angeles', name: 'Chargers', stadium: 'SoFi Stadium', blurb: 'Southern California speedsters known for lightning-strike passing attacks.', conference: 'AFC', division: 'West', colors: { primary: '#0080C6', secondary: '#FFC20E' }, stats: mockStats(16) },
  { id: 'dal', abbr: 'DAL', city: 'Dallas', name: 'Cowboys', stadium: 'AT&T Stadium', blurb: "'America's Team,' with a star on the helmet and championship history to match.", conference: 'NFC', division: 'East', colors: { primary: '#041E42', secondary: '#869397' }, stats: mockStats(17) },
  { id: 'nyg', abbr: 'NYG', city: 'New York', name: 'Giants', stadium: 'MetLife Stadium', blurb: 'A charter NFL franchise built on hard-nosed defense and clutch playoff runs.', conference: 'NFC', division: 'East', colors: { primary: '#0B2265', secondary: '#A71930' }, stats: mockStats(18) },
  { id: 'phi', abbr: 'PHI', city: 'Philadelphia', name: 'Eagles', stadium: 'Lincoln Financial Field', blurb: "Philadelphia's fiercely loyal fans back an offense built to soar through the NFC.", conference: 'NFC', division: 'East', colors: { primary: '#004C54', secondary: '#A5ACAF' }, stats: mockStats(19) },
  { id: 'was', abbr: 'WAS', city: 'Washington', name: 'Commanders', stadium: 'Northwest Stadium', blurb: "Washington's storied franchise, rebuilding its identity in the nation's capital.", conference: 'NFC', division: 'East', colors: { primary: '#5A1414', secondary: '#FFB612' }, stats: mockStats(20) },
  { id: 'chi', abbr: 'CHI', city: 'Chicago', name: 'Bears', stadium: 'Soldier Field', blurb: "The NFC's oldest continuously run franchise, rooted in bruising, defense-first football.", conference: 'NFC', division: 'North', colors: { primary: '#0B162A', secondary: '#C83803' }, stats: mockStats(21) },
  { id: 'det', abbr: 'DET', city: 'Detroit', name: 'Lions', stadium: 'Ford Field', blurb: "Detroit's resilient roar, finally turning decades of patience into real contention.", conference: 'NFC', division: 'North', colors: { primary: '#0076B6', secondary: '#B0B7BC' }, stats: mockStats(22) },
  { id: 'gb', abbr: 'GB', city: 'Green Bay', name: 'Packers', stadium: 'Lambeau Field', blurb: "The league's only fan-owned team, playing outdoors on Wisconsin's frozen tundra.", conference: 'NFC', division: 'North', colors: { primary: '#203731', secondary: '#FFB612' }, stats: mockStats(23) },
  { id: 'min', abbr: 'MIN', city: 'Minnesota', name: 'Vikings', stadium: 'U.S. Bank Stadium', blurb: "Minnesota's purple-clad squad, known for explosive passing and a deafening dome crowd.", conference: 'NFC', division: 'North', colors: { primary: '#4F2683', secondary: '#FFC62F' }, stats: mockStats(24) },
  { id: 'atl', abbr: 'ATL', city: 'Atlanta', name: 'Falcons', stadium: 'Mercedes-Benz Stadium', blurb: "Atlanta's high-flying offense looks to finally land the franchise's first title.", conference: 'NFC', division: 'South', colors: { primary: '#A71930', secondary: '#000000' }, stats: mockStats(25) },
  { id: 'car', abbr: 'CAR', city: 'Carolina', name: 'Panthers', stadium: 'Bank of America Stadium', blurb: "Carolina's newer-generation franchise, built around big-play athletes on both sides.", conference: 'NFC', division: 'South', colors: { primary: '#0085CA', secondary: '#101820' }, stats: mockStats(26) },
  { id: 'no', abbr: 'NO', city: 'New Orleans', name: 'Saints', stadium: 'Caesars Superdome', blurb: "New Orleans' beloved 'Who Dat' nation, forever tied to a magical 2009 title run.", conference: 'NFC', division: 'South', colors: { primary: '#D3BC8D', secondary: '#101820' }, stats: mockStats(27) },
  { id: 'tb', abbr: 'TB', city: 'Tampa Bay', name: 'Buccaneers', stadium: 'Raymond James Stadium', blurb: "Tampa Bay's pirate-themed squad, capable of flashes of championship-level football.", conference: 'NFC', division: 'South', colors: { primary: '#D50A0A', secondary: '#34302B' }, stats: mockStats(28) },
  { id: 'ari', abbr: 'ARI', city: 'Arizona', name: 'Cardinals', stadium: 'State Farm Stadium', blurb: "The NFL's oldest continuously operating franchise, now based in the Arizona desert.", conference: 'NFC', division: 'West', colors: { primary: '#97233F', secondary: '#000000' }, stats: mockStats(29) },
  { id: 'lar', abbr: 'LAR', city: 'Los Angeles', name: 'Rams', stadium: 'SoFi Stadium', blurb: "Los Angeles' 'greatest show' revival, blending flash with championship pedigree.", conference: 'NFC', division: 'West', colors: { primary: '#003594', secondary: '#FFA300' }, stats: mockStats(30) },
  { id: 'sf', abbr: 'SF', city: 'San Francisco', name: '49ers', stadium: "Levi's Stadium", blurb: "San Francisco's dynasty franchise, built on precision and Bay Area innovation.", conference: 'NFC', division: 'West', colors: { primary: '#AA0000', secondary: '#B3995D' }, stats: mockStats(31) },
  { id: 'sea', abbr: 'SEA', city: 'Seattle', name: 'Seahawks', stadium: 'Lumen Field', blurb: "The '12th Man' crowd noise fuels one of football's rowdiest home fields.", conference: 'NFC', division: 'West', colors: { primary: '#002244', secondary: '#69BE28' }, stats: mockStats(32) },
]

export function getTeam(id: string): Team | undefined {
  return teams.find((t) => t.id === id)
}