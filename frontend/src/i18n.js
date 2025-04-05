import i18n from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { initReactI18next } from 'react-i18next';

// We'll load translations later, for now just configure the basics
const resources = {
    en: {
        translation: {
            // Navigation & Common
            "nav.home": "Home",
            "nav.dashboard": "Dashboard",
            "nav.myChats": "My Chats",
            "nav.adminDashboard": "Admin Dashboard",
            "nav.createListing": "Create Listing",
            "nav.myFavorites": "My Favorites",
            "nav.editProfile": "Edit Profile",
            "nav.logout": "Logout",
            "nav.login": "Login",
            "nav.register": "Register",
            "footer.brand": "HouseHunter",
            "error.notFound": "404 - Page Not Found",
            // Add more keys as needed for forms, buttons etc.
        }
    },
    fr: {
        translation: {
            // Navigation & Common
            "nav.home": "Accueil",
            "nav.dashboard": "Tableau de Bord",
            "nav.myChats": "Mes Discussions",
            "nav.adminDashboard": "Tableau Admin",
            "nav.createListing": "Créer une Annonce",
            "nav.myFavorites": "Mes Favoris",
            "nav.editProfile": "Modifier le Profil",
            "nav.logout": "Déconnexion",
            "nav.login": "Connexion",
            "nav.register": "S'inscrire",
            "footer.brand": "HouseHunter", // Keep brand name or translate if desired
            "error.notFound": "404 - Page Non Trouvée",
            // Add more keys as needed for forms, buttons etc.
        }
    }
};

i18n
    // Detect user language
    .use(LanguageDetector)
    // Pass the i18n instance to react-i18next.
    .use(initReactI18next)
    // Init i18next
    .init({
        debug: true, // Set to false in production
        fallbackLng: 'en',
        interpolation: {
            escapeValue: false, // React already safes from xss
        },
        resources: resources,
        // Language detection options
        detection: {
            order: ['querystring', 'cookie', 'localStorage', 'sessionStorage', 'navigator', 'htmlTag', 'path', 'subdomain'],
            caches: ['localStorage', 'cookie'],
        }
    });

export default i18n;