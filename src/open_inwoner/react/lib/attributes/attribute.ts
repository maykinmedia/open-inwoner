import { BooleanLike } from '@react/types/attributes';

export const normalizeBoolean = (value: BooleanLike) =>
  value === true || value === 'true';
