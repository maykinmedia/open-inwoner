import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { Button } from '../Button/Button';
import './Card.scss';

interface ProductCardProps {
    title: string,
    to: string,
    summary: string,
}

export function ProductCard(props:ProductCardProps) {
  return (
    <div className="card card--product">
      <h3 className="card__title">{ props.title }</h3>
      <p className="card__summary">{ props.summary }</p>
      <Button href={props.to} transparent>
        <ArrowForwardIcon />
      </Button>
    </div>
  );
}
