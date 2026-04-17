import { render, screen } from '@testing-library/react';

function Greeting({ name }: { name: string }) {
  return <p>Hello, {name}</p>;
}

it('renders greeting', () => {
  render(<Greeting name="AP CSA" />);
  expect(screen.getByText('Hello, AP CSA')).toBeInTheDocument();
});
