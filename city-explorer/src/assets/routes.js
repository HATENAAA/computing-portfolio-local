import records from '../../../assets/evidence/city-places.json';
const byId = new Map(records.places.map(place => [place.id, place.position]));
export const routes = Object.fromEntries(records.routes.map(route => [route.id, route.stops.map(id => byId.get(id))]));
