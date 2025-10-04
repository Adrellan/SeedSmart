import { createSlice } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

export function getLocalStorageData() {
	const data = localStorage.getItem('mapState');
	if (!data) return null;
	const parsed = JSON.parse(data);
	return parsed;
}

interface MapState {
	coordinates: {
		lat: number,
		lng: number,
	},
	zoom: number,
}


const initialState: MapState = getLocalStorageData() || {
	coordinates: {
		lat: 47.1625, // Magyarország középpontja
		lng: 19.5033, // Magyarország középpontja
	},
	zoom: 8,
};

export const mapSlice = createSlice({
	name: 'map',
	initialState,
	reducers: {
		setCoordinates(state, {payload}: PayloadAction<typeof initialState.coordinates>){
			state.coordinates = payload;
		},
		setZoom(state, { payload }: PayloadAction<number>) {
			state.zoom = payload;
		}
	},
})

export const { setCoordinates, setZoom } = mapSlice.actions
export const mapReducer = mapSlice.reducer;