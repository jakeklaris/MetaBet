import React from 'react';
import PropTypes from 'prop-types';
import { Button } from 'semantic-ui-react'

export default class Poll extends React.Component {
  /* Display number of image and post owner of a single post
   */
  constructor(props) {
    // Initialize mutable state
    super(props);
    this.state = { description: '', choices: [], endTime: ''};
  }

  componentDidMount() {
    // This line automatically assigns this.props.url to the const variable url
    const { url } = this.props;
    // Call REST API to get the post's information
    fetch(url, { credentials: 'same-origin' })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        this.setState({
          choices: data.choices,
          description: data.owner,
          endTime: data.endTime
        });
      })
      .catch((error) => console.log(error));
  }

  render() {
    // This line automatically assigns this.state.imgUrl to the const variable imgUrl
    // and this.state.owner to the const variable owner
    const { description, choices, endTime } = this.state;
    // Render number of post image and post owner
    return (
      <div className="poll">
        <Button>Click Me</Button>
      </div>
    );
  }
}
