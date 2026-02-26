/**
 * Returns a query string based on params.
 * @param params Params (parameters) object.
 * @return query A (serialized) query string.
 */
export const serializeParams = (params: Record<string, string | string[]>) => {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, values]) => {
    if (values && Array.isArray(values))
      values.forEach((value) => searchParams.append(key, value));
    else searchParams.append(key, values);
  });

  return searchParams;
};
