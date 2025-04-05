import React from 'react';
import { useTranslation } from 'react-i18next';

const LanguageSwitcher = () => {
    const { i18n } = useTranslation();

    const changeLanguage = (lng) => {
        i18n.changeLanguage(lng);
    };

    // Basic styling for the buttons
    const buttonStyle = {
        marginLeft: '5px',
        padding: '5px 10px',
        cursor: 'pointer',
        border: '1px solid #ccc',
        backgroundColor: '#f0f0f0',
    };

    const activeButtonStyle = {
        ...buttonStyle,
        backgroundColor: '#ddd',
        fontWeight: 'bold',
    };

    return (
        <div style={{ marginLeft: 'auto' }}> {/* Pushes switcher to the right */}
            <button
                style={i18n.language === 'en' ? activeButtonStyle : buttonStyle}
                onClick={() => changeLanguage('en')}
                disabled={i18n.language === 'en'}
            >
                EN
            </button>
            <button
                style={i18n.language === 'fr' ? activeButtonStyle : buttonStyle}
                onClick={() => changeLanguage('fr')}
                disabled={i18n.language === 'fr'}
            >
                FR
            </button>
        </div>
    );
};

export default LanguageSwitcher;