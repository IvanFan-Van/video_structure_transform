import { createContext, useContext } from "react";

export type TourLang = "en" | "zh";

export const TourLangContext = createContext<TourLang>("en");

export function useTourLang() {
    return useContext(TourLangContext);
}
