import * as fop from '@fiftyone/plugins'
import * as fos from '@fiftyone/state'
import {Button, useTheme, Selector, ErrorBoundary} from '@fiftyone/components'
import {useRecoilValue, useRecoilSnapshot } from 'recoil'
import React, {useEffect, useState} from 'react'
import { Inspector } from 'react-inspector';




const Value: React.FC<{ value: string; className: string }> = ({ value }) => {
  return <>{value}</>;
};
const ContentValue: React.FC<{ value: string; className: string }> = ({ value }) => {
  return <>{value.key}</>;
};

function Container({children}) {
  return (
    <div style={{margin: '2rem'}}>{children}</div>
  )
}
function useSearch(choices, {toValue, toKey, toSearchable} = {}) {
  const [choice, setChoice] = useState(null);

  if (typeof toKey !== 'function') {
    toKey = (item) => item
    toValue = (item) => item
    toSearchable = toValue = (item) => item
  }

  const handlers = {
    onSelect(selected) {
      setChoice(selected);
    },
    value: choice !== null ? toValue(choice) : null,
    toKey: toKey,
    useSearch: (search) => ({
      values:
        choices.filter((item) =>
          toSearchable(item).toLowerCase().includes(search.toLowerCase())
        ),
    }),
  };

  return {
    choice,
    hasChoice: choice !== null,
    handlers
  }
}

function useDebugger() {
  const snapshot = useRecoilSnapshot();
  const [state, setState] = React.useState({values: new Map()});
  const rawKeys = Array.from(state.values.keys());
  const parsedKeys = rawKeys.map((key) => parseKey(key));
  const names = Array.from(new Set(parsedKeys.map((key) => key.name)));
  const contents = rawKeys.map(key => {
    const item = state.values.get(key)
    const str = JSON.stringify(item.loadable.contents)
    return {key, parsedKey: parseKey(key), str, changed: item.changed, loadable: item.loadable}
  }).sort((a, b) => b.changed - a.changed)
  function clearState() {
    setState({values: new Map()})
  }
  useEffect(() => {
    setState(previousState => {
      const newValues = new Map(previousState.values);
      for (const node of snapshot.getNodes_UNSTABLE()) {
        newValues.set(node.key, {
          loadable: snapshot.getLoadable(node),
          changed: Date.now()
        });
      }
      return {
        values: new Map(newValues)
      }
    })
  }, [snapshot]);
  const searchNames = useSearch(names)
  const searchContents = useSearch(contents, {
    toValue: (item) => item.key,
    toKey: (item) => item.key,
    toSearchable: (item) => item.str
  })

  return {
    values: state.values,
    searchNames,
    searchContents,
    contents,
    clearState
  }
}

function DebugObserver() {
  const theme = useTheme();
  const dbg = useDebugger();
  

  const selectorStyle = {
    background: theme.neutral.softBg,
    borderTopLeftRadius: 3,
    borderTopRightRadius: 3,
    padding: "0.25rem",
  };

  return (
    <div>
        <Button onClick={dbg.clearState}>Clear</Button>

        <Selector
          {...dbg.searchNames.handlers}
          placeholder={"Search for an Atom or Selector"}
          overflow={true}
          component={Value}
          containerStyle={selectorStyle}
        />
        <Selector
          {...dbg.searchContents.handlers}
          placeholder={"Search State Content"}
          overflow={true}
          component={ContentValue}
          containerStyle={selectorStyle}
        />
        {
          dbg.contents.map(item => <SnapshotKey item={item} />)
        }
    </div>
  )
}

export function Debugger() {
  const [state, setState] = React.useState();

  useEffect(() => {
    if (state === 'refresh') {
      setState('refreshing')
      setTimeout(() => {
        setState('refreshed')
      }, 1000)
    }
    if (state === 'refreshed') {
      setState(null)
    }
  }, [state])

  if (state === 'refresh') {
    return (
      <h3>refreshing...</h3>
    )
  }

  return (
    <Container>
      <h1>Debugger <Button onClick={() => setState('refresh')}>Refresh</Button></h1>
      <ErrorBoundary>
        <DebugObserver />
      </ErrorBoundary>
    </Container>
    
  )
}

function SnapshotKey({item}) {
  const isObject = typeof item.loadable.contents === 'object'
  return (
    <div>
      <h2>{item.parsedKey.name} {!isObject && JSON.stringify(item.loadable.contents)}</h2>
      {item.parsedKey.hasInput && <h4>Input</h4>}
      {item.parsedKey.hasInput && <Contents raw={item.parsedKey.parsedInput} />}
      {item.loadable.contents && <h4>Contents</h4>}
      {isObject && <Contents raw={item.loadable.contents} />}
    </div>
  )
}

function Contents({raw}) {
  return (
    <Inspector expandLevel={3} theme="chromeDark" data={raw} />
  )
}

function parseKey(key) {
  const parts = key.split('__')
  const name = parts[0]
  const isWrapper = parts[1] === 'Wrapper'
  const selectorFamilyIdx = isWrapper ? 2 : 1
  const hasSelectorFamilyInfo = !!parts[selectorFamilyIdx]
  const isSelectorFamily = hasSelectorFamilyInfo && parts[selectorFamilyIdx].startsWith('selectorFamily')
  const input = isSelectorFamily
    ? parts[selectorFamilyIdx].split('/')[1]
    : parts[1]
  const hasInput = !!input
  
  return {
    name,
    isWrapper,
    isSelectorFamily,
    hasInput: !!input,
    parsedInput: hasInput ? JSON.parse(input) : null
  }
}