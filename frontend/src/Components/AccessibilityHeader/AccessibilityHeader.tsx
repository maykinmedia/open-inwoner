import React, {ReactElement, useRef, useState} from 'react';
import FontDownloadOutlinedIcon from '@mui/icons-material/FontDownloadOutlined';
import HearingOutlinedIcon from '@mui/icons-material/HearingOutlined';
import PrintOutlinedIcon from '@mui/icons-material/PrintOutlined';
import ZoomInOutlinedIcon from '@mui/icons-material/ZoomInOutlined';
import ZoomOutOutlinedIcon from '@mui/icons-material/ZoomOutOutlined';
import {Link} from '../Typography/Link';
import './AccessibilityHeader.scss';


/**
 * Header containing various accessibility features.
 * @return {ReactElement}
 */
export function AccessibilityHeader(): ReactElement {
  const speechSynthesis = (typeof window === 'object') ? window['speechSynthesis'] : null;
  const SpeechSynthesisUtterance = (typeof window === 'object') ? window['SpeechSynthesisUtterance'] : null;
  const isSpeechSynthesisSupported = Boolean(speechSynthesis && SpeechSynthesisUtterance);
  const utteranceRef = useRef<{ current: SpeechSynthesisUtterance | null }>(null);
  const [previousFontSize, setPreviousFontSize] = useState<string | null>(null);
  const [previousFontFamily, setPreviousFontFamily] = useState<string | null>(null);

  /**
   * Runs text to speech ont the textContent of <main>.
   */
  const textToSpeech = (): void => {
    if (!isSpeechSynthesisSupported) {
      return
    }

    const main = (typeof document === 'undefined') ? null : document.querySelector('main');
    const mainTextContent = main?.textContent;

    if (!utteranceRef.current) {
      // @ts-ignore
      utteranceRef.current = new SpeechSynthesisUtterance('');
    }
    const utterance = utteranceRef?.current as any;
    utterance.text = mainTextContent;
    speechSynthesis?.speak(utterance);
  }

  /**
   * Toggles zoom of regular text.
   */
  const zoom = (): void => {
    const target = document.querySelector(':root') as HTMLElement;
    const varName = '--font-size-body';

    if (!target) {
      return;
    }

    if (previousFontSize) {
      target.style.removeProperty(varName);
      setPreviousFontSize(null);
      return;
    }

    const currentFontSize = getComputedStyle(target).getPropertyValue(varName).trim()
    const currentFontSizeValue = parseInt(currentFontSize);
    const currentFontSizeUnitMatch = currentFontSize.match(/[^\d]+/);
    const currentFontSizeUnit = (currentFontSizeUnitMatch) ? currentFontSizeUnitMatch[0] : '';
    const newFontSizeValue = currentFontSizeValue * 1.2;
    const newFontSize = `${newFontSizeValue}${currentFontSizeUnit}`;

    setPreviousFontSize(currentFontSize);
    target?.style.setProperty(varName, newFontSize);
  }

  /**
   * Swaps the font for a set of font more optimized for people with Dyslexia.
   */
  const swapFont = (): void => {
    const target = document.querySelector(':root') as HTMLElement;
    const varName = '--font-family-body';
    const alternativeFontFamily = `Helvetica, Courier, Arial, Verdana.`;

    if (!target) {
      return;
    }

    if (previousFontFamily) {
      target.style.removeProperty(varName);
      setPreviousFontFamily(null);
      return;
    }

    const currentFontFamily = getComputedStyle(target).getPropertyValue(varName).trim()

    setPreviousFontFamily(currentFontFamily);
    target?.style.setProperty(varName, alternativeFontFamily);
  }

  return (
    <header className="accessibility-header">
      <ul className="accessibility-header__list">
        {isSpeechSynthesisSupported && <li className="accessibility-header__list-item">
          <Link to="#" icon={HearingOutlinedIcon} onClick={textToSpeech}>Lees voor</Link>
        </li>}

        <li className="accessibility-header__list-item">
          <Link to="#" icon={(previousFontSize) ? ZoomOutOutlinedIcon : ZoomInOutlinedIcon} onClick={zoom}>
            Vergroten
          </Link>
        </li>

        <li className="accessibility-header__list-item">
          <Link to="#" icon={FontDownloadOutlinedIcon} onClick={swapFont}>
            {(previousFontFamily) ? 'Normaal lettertype' : 'Dyslexie'}
          </Link>
        </li>

        <li className="accessibility-header__list-item">
          <Link to="javascript:print()" icon={PrintOutlinedIcon}>Print pagina</Link>
        </li>
      </ul>
    </header>
  )
}
